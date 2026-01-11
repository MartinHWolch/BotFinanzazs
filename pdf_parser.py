import pdfplumber
import os
import json
from typing import List, Dict, Optional
from config import PDF_PASSWORD

class PDFParser:
    def __init__(self, password: Optional[str] = PDF_PASSWORD):
        self.password = password

    def extract_content(self, pdf_path: str) -> Dict[str, any]:
        """
        Extracts both text and tables from a PDF.
        Handles decryption if password is set.
        Saves parsed content to outputs/ for inspection.
        """
        text_content = ""
        tables_content = []

        try:
            with pdfplumber.open(pdf_path, password=self.password) as pdf:
                print(f"Successfully opened {pdf_path}")
                for page_num, page in enumerate(pdf.pages, 1):
                    print(f"  Processing page {page_num}...")
                    # Extract text
                    page_text = page.extract_text()
                    if page_text:
                        text_content += f"\n=== PAGE {page_num} ===\n"
                        text_content += page_text + "\n"
                    
                    # Extract tables
                    page_tables = page.extract_tables()
                    if page_tables:
                        for table_idx, table in enumerate(page_tables, 1):
                            # Clean up None values in tables
                            clean_table = [[cell if cell is not None else "" for cell in row] for row in table]
                            tables_content.append({
                                "page": page_num,
                                "table_index": table_idx,
                                "data": clean_table
                            })
                        
        except Exception as e:
            print(f"Error parsing PDF {pdf_path}: {e}")
            if "Password" in str(e):
                print("Hint: Check if PDF_PASSWORD is correct in .env")
            return None

        # DEBUG: Save raw table structure for inspection
        self._save_table_debug(pdf_path, tables_content)

        return {
            "text": text_content,
            "tables": tables_content
        }
    
    def _save_table_debug(self, pdf_path: str, tables_content: List):
        """Save raw table structure as JSON for debugging."""
        import json
        
        base_name = os.path.basename(pdf_path)
        debug_name = f"{os.path.splitext(base_name)[0]}_TABLE_DEBUG.json"
        debug_path = os.path.join("outputs", debug_name)
        
        if not os.path.exists("outputs"):
            os.makedirs("outputs")
        
        # Convert to JSON-serializable format
        debug_data = {
            "total_tables": len(tables_content),
            "tables": []
        }
        
        for table_info in tables_content:
            debug_data["tables"].append({
                "page": table_info["page"],
                "table_index": table_info["table_index"],
                "rows": len(table_info["data"]),
                "columns": len(table_info["data"][0]) if table_info["data"] else 0,
                #"first_6_rows": table_info["data"][:6] if table_info["data"] else [],
                "all_data": table_info["data"]  # Full data for inspection
            })
        
        with open(debug_path, 'w', encoding='utf-8') as f:
            json.dump(debug_data, f, indent=2, ensure_ascii=False)
        
        print(f"  🔍 DEBUG: Table structure saved to {debug_path}")
