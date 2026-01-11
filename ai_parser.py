import os
import json
from groq import Groq
from typing import List, Dict
from datetime import date
from models import Transaction

class AIParser:
    """Use Groq AI to parse transaction data from cartola text."""
    
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.3-70b-versatile"  # Groq's best model
    
    def parse_transactions(self, text: str, current_year: int = 2025) -> List[Transaction]:
        """
        Use Groq AI to extract and structure transactions from cartola text.
        Returns a list of Transaction objects.
        """
        print("🤖 Using AI to parse transactions...")
        
        prompt = self._build_prompt(text, current_year)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un experto en análisis de estados de cuenta bancarios chilenos. Tu tarea es extraer transacciones de texto de cartolas del Banco de Chile y estructurarlas en formato JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Low temperature for consistent parsing
                max_tokens=4000
            )
            
            result_text = response.choices[0].message.content
            
            # Extract JSON from response (might be wrapped in markdown code blocks)
            json_start = result_text.find('[')
            json_end = result_text.rfind(']') + 1
            
            if json_start == -1 or json_end == 0:
                print("  ⚠️  Could not find JSON in AI response")
                return []
            
            json_str = result_text[json_start:json_end]
            transactions_data = json.loads(json_str)
            
            # Convert to Transaction objects
            transactions = []
            for t in transactions_data:
                try:
                    # Parse date
                    date_parts = t['fecha'].split('-')
                    trans_date = date(int(date_parts[0]), int(date_parts[1]), int(date_parts[2]))
                    
                    transactions.append(Transaction(
                        date=trans_date,
                        description=t['descripcion'],
                        amount=float(t['monto']),
                        type=t['tipo']
                    ))
                except Exception as e:
                    print(f"  ⚠️  Error parsing transaction: {e}")
                    continue
            
            print(f"  ✅ AI extracted {len(transactions)} transactions")
            return transactions
            
        except Exception as e:
            print(f"  ❌ AI parsing error: {e}")
            return []
    
    def _build_prompt(self, text: str, current_year: int) -> str:
        """Build the prompt for Groq AI."""
        return f"""Analiza el siguiente texto extraído de una cartola del Banco de Chile y extrae TODAS las transacciones.

CONTEXTO:
- Año: {current_year}
- Los montos en Chile usan punto como separador de miles (ej: 1.234.567 = un millón)
- NO hay decimales/centavos en pesos chilenos
- Formato de fecha en cartola: DD/MM

REGLAS DE CLASIFICACIÓN:
- "PAGO:", "GIRO", "IMPUESTO", "PRIMA", "TRASPASO A:", "AMORTIZACION" → tipo: "egreso"
- "TRANSFERENCIA DESDE", "TRASPASO DE:", "ABONO" → tipo: "ingreso"

FORMATO DE SALIDA (JSON array):
[
  {{
    "fecha": "YYYY-MM-DD",
    "descripcion": "descripción completa",
    "monto": número_entero_sin_puntos,
    "tipo": "ingreso" o "egreso"
  }}
]

IMPORTANTE:
- Extrae SOLO transacciones reales (ignora headers, totales, resúmenes)
- Los montos deben ser números enteros SIN puntos de miles
- Cada transacción debe tener fecha visible en el formato DD/MM
- Si la fecha es DD/MM, asume año {current_year}

TEXTO DE LA CARTOLA:
{text[:8000]}

Responde SOLO con el JSON array, sin explicaciones adicionales."""
    
