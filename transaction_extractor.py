import re
import pandas as pd
from typing import List, Dict
from datetime import datetime, date
from models import Transaction

class TransactionExtractor:
    def __init__(self):
        self.current_year = 2025  # Can be extracted from PDF metadata or config
    
    def extract_transactions(self, parsed_data: Dict[str, any]) -> List[Transaction]:
        """
        Extract transactions using AI (Groq) for robust parsing.
        Falls back to manual text parsing if AI fails.
        """
        transactions = []
        
        # Strategy 1: AI parsing (primary - most accurate)
        if parsed_data.get("text"):
            try:
                from ai_parser import AIParser
                ai_parser = AIParser()
                print("Attempting AI-powered extraction...")
                transactions = ai_parser.parse_transactions(
                    parsed_data["text"], 
                    self.current_year
                )
            except Exception as e:
                print(f"  ⚠️  AI parsing failed: {e}")
                print("  Falling back to manual parsing...")
        
        # Strategy 2: Manual text parsing (fallback)
        if not transactions and parsed_data.get("text"):
            print("Extracting from text (manual Banco Chile parser)...")
            transactions = self._extract_from_text_banco_chile(parsed_data["text"])
        
        # Strategy 3: Table parsing (last resort)
        if not transactions and parsed_data.get("tables"):
            print("Attempting table extraction...")
            transactions = self._extract_from_tables_pandas(parsed_data["tables"])
        
        return transactions
    
    def _extract_from_tables_pandas(self, tables_data: List[Dict]) -> List[Transaction]:
        """
        Use pandas to process tables from Banco Chile cartola.
        Expected columns: DÍA/MES | DETALLE | SUCURSAL | N°DOCTO | CHEQUES/CARGOS | DEPOSITOS/ABONOS | SALDO
        """
        all_transactions = []
        
        for table_info in tables_data:
            table_data = table_info["data"]
            
            if not table_data or len(table_data) < 2:
                continue
            
            # Clean None values - replace with empty strings
            cleaned_data = []
            for row in table_data:
                cleaned_row = [str(cell) if cell is not None else "" for cell in row]
                cleaned_data.append(cleaned_row)
            
            # Convert to DataFrame
            df = pd.DataFrame(cleaned_data)
            
            # Find header row (contains keywords like DETALLE, CARGO, ABONO)
            header_idx = self._find_header_row(df)
            
            if header_idx is not None:
                # Use found header
                df.columns = df.iloc[header_idx]
                df = df.iloc[header_idx + 1:]  # Data starts after header
            else:
                # Assign generic column names based on typical structure
                # [Fecha, Detalle, Sucursal, N°Doc, Cargo, Abono, Saldo]
                if len(df.columns) >= 6:
                    df.columns = ['FECHA', 'DETALLE', 'SUCURSAL', 'NDOC', 'CARGO', 'ABONO', 'SALDO'][:len(df.columns)]
                else:
                    continue  # Not enough columns
            
            # Clean and process
            df = df.reset_index(drop=True)
            
            # Identify key columns (flexible matching)
            fecha_col = self._find_column(df, ['fecha', 'dia', 'dia/mes'])
            detalle_col = self._find_column(df, ['detalle', 'descripcion', 'transaccion'])
            cargo_col = self._find_column(df, ['cargo', 'cheques', 'debito', 'monto cheques'])
            abono_col = self._find_column(df, ['abono', 'deposito', 'credito', 'monto depositos'])
            
            if not all([fecha_col, detalle_col]):
                print(f"  ⚠️  Could not identify required columns in table")
                continue
            
            # Process each row
            for idx, row in df.iterrows():
                try:
                    # Skip empty rows
                    if row[fecha_col] is None or str(row[fecha_col]).strip() == '':
                        continue
                    
                    # Skip summary rows
                    detalle_text = str(row[detalle_col]).lower()
                    if any(word in detalle_text for word in ['total', 'saldo final', 'saldo anterior', 'retencion']):
                        continue
                    
                    # Parse date
                    fecha_str = str(row[fecha_col]).strip()
                    fecha = self._parse_date_banco_chile(fecha_str, self.current_year)
                    
                    if not fecha:
                        continue
                    
                    # Get description
                    descripcion = str(row[detalle_col]).strip()
                    if not descripcion or descripcion == 'nan':
                        continue
                    
                    # Get amounts
                    cargo = 0.0
                    abono = 0.0
                    
                    if cargo_col and row[cargo_col]:
                        cargo = self._parse_amount(str(row[cargo_col]))
                    
                    if abono_col and row[abono_col]:
                        abono = self._parse_amount(str(row[abono_col]))
                    
                    # Create transaction
                    if cargo > 0:
                        all_transactions.append(Transaction(
                            date=fecha,
                            description=descripcion,
                            amount=cargo,
                            type="egreso"
                        ))
                    
                    if abono > 0:
                        all_transactions.append(Transaction(
                            date=fecha,
                            description=descripcion,
                            amount=abono,
                            type="ingreso"
                        ))
                
                except Exception as e:
                    print(f"  ⚠️  Error processing row {idx}: {e}")
                    continue
        
        print(f"  ✓ Extracted {len(all_transactions)} transactions")
        return all_transactions
    
    def _find_header_row(self, df: pd.DataFrame) -> int:
        """Find the row that contains column headers."""
        for idx, row in df.iterrows():
            row_text = ' '.join([str(cell).lower() for cell in row if cell])
            if any(keyword in row_text for keyword in ['detalle', 'cargo', 'abono', 'dia/mes', 'fecha']):
                return idx
        return None
    
    def _find_column(self, df: pd.DataFrame, keywords: List[str]) -> str:
        """Find column name that matches any of the keywords."""
        for col in df.columns:
            col_lower = str(col).lower().strip()
            for keyword in keywords:
                if keyword in col_lower:
                    return col
        return None
    
    def _parse_date_banco_chile(self, date_str: str, default_year: int = 2025) -> date:
        """Parse Banco Chile date format (DD/MM or DD/MM/YY or DD/MM/YYYY)."""
        if not date_str or date_str == 'nan':
            return None
        
        date_str = date_str.strip()
        
        try:
            parts = date_str.split('/')
            if len(parts) == 2:
                day = int(parts[0])
                month = int(parts[1])
                return date(default_year, month, day)
            elif len(parts) == 3:
                day = int(parts[0])
                month = int(parts[1])
                year = int(parts[2])
                if year < 100:
                    year = 2000 + year if year < 50 else 1900 + year
                return date(year, month, day)
        except:
            pass
        
        return None
    
    def _parse_amount(self, amount_str: str) -> float:
        """
        Parse Chilean format amounts: 1.234.567,89 or 1.234.567
        Returns positive value only.
        """
        # Handle various null/empty representations
        if not amount_str or amount_str in ['nan', '', 'None', 'none', 'NULL']:
            return 0.0
        
        # Remove currency symbols and whitespace
        amount_str = str(amount_str).replace('$', '').replace(' ', '').strip()
        
        if not amount_str or amount_str == '-' or amount_str == '.':
            return 0.0
        
        try:
            # Chilean format: . for thousands, , for decimals
            # Remove thousands separator
            amount_str = amount_str.replace('.', '')
            # Replace decimal separator
            amount_str = amount_str.replace(',', '.')
            # Remove any remaining non-numeric except decimal point and minus
            amount_str = re.sub(r'[^\d.-]', '', amount_str)
            
            if not amount_str or amount_str == '-':
                return 0.0
            
            value = abs(float(amount_str))
            return value
        except:
            return 0.0
    
    def _extract_from_text_banco_chile(self, text: str) -> List[Transaction]:
        """
        Extract transactions from Banco Chile cartola text.
        Format: DETALLE followed by amounts, separated by newlines.
        """
        transactions = []
        lines = text.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines and headers
            if not line or 'DETALLE DE TRANSACCION' in line or 'SUCURSAL' in line or 'MONTO CHEQUES' in line:
                i += 1
                continue
            
            # Look for transaction patterns
            # Banco Chile format: "PAGO:MERCHANT CE" or "TRANSFERENCIA..." or "TRASPASO..."
            if any(keyword in line for keyword in ['PAGO:', 'TRANSFERENCIA', 'TRASPASO', 'ABONO', 'AVANCE', 'AMORTIZACION', 'PRIMA', 'IMPUESTO', 'INTERESES', 'GIRO']):
                descripcion = line
                
                # Try to find amount in next few lines
                cargo = 0.0
                abono = 0.0
                
                # Look ahead for amounts (usually within next 3-5 lines)
                for j in range(i + 1, min(i + 6, len(lines))):
                    next_line = lines[j].strip()
                    
                    # Skip sucursal codes
                    if next_line in ['CENTRAL', 'NTRAL', 'ERNET', 'INTERNET']:
                        continue
                    
                    # Try to parse as amount
                    amount = self._parse_amount(next_line)
                    if amount > 0:
                        # Heuristic: first amount is usually cargo, but we need context
                        # For PAGO, GIRO, IMPUESTO, PRIMA → cargo (egreso)
                        # For TRANSFERENCIA DESDE, TRASPASO DE, ABONO → abono (ingreso)
                        
                        if any(word in descripcion for word in ['TRANSFERENCIA DESDE', 'TRASPASO DE:', 'ABONO']):
                            abono = amount
                        else:
                            cargo = amount
                        break
                
                # Create transaction if we have an amount
                if cargo > 0:
                    transactions.append(Transaction(
                        date=date(self.current_year, 12, 1),  # Default date, should extract from PDF header
                        description=descripcion[:100],
                        amount=cargo,
                        type="egreso"
                    ))
                elif abono > 0:
                    transactions.append(Transaction(
                        date=date(self.current_year, 12, 1),
                        description=descripcion[:100],
                        amount=abono,
                        type="ingreso"
                    ))
            
            i += 1
        
        print(f"  ✓ Extracted {len(transactions)} transactions from text")
        return transactions
    
    def _extract_from_text(self, text: str) -> List[Transaction]:
        """Fallback generic text extraction."""
        # Keep for compatibility, but Banco Chile uses specific parser above
        return self._extract_from_text_banco_chile(text)
