import time
import json
import os
from datetime import date
from email_reader import EmailReader
from pdf_parser import PDFParser
from transaction_extractor import TransactionExtractor
from categorizer import Categorizer
from models import Statement
from report_generator import ReportGenerator
from file_tracker import FileTracker

class FinancialBot:
    def __init__(self):
        self.reader = EmailReader()
        self.parser = PDFParser()
        self.extractor = TransactionExtractor()
        self.categorizer = Categorizer()
        self.report_generator = ReportGenerator()
        self.file_tracker = FileTracker()

    def run(self):
        """Single execution run - process all matching emails once."""
        print("Starting Financial Bot (Single Run Mode)...")
        print(f"📂 Previously processed files: {self.file_tracker.get_stats()['total_processed']}\n")
        
        # Fetch all matching emails (not just unread)
        emails = self.reader.fetch_unread_emails()
        
        if not emails:
            print("✅ No new emails found matching criteria.")
            return
        
        print(f"Found {len(emails)} email(s) to process.\n")
        
        processed_count = 0
        skipped_count = 0
        
        for email_obj in emails:
            print(f"\n{'='*60}")
            print(f"📧 Email: {email_obj.subject}")
            print(f"{'='*60}")
            
            for attachment_path in email_obj.attachments:
                # Check if already processed
                if self.file_tracker.is_processed(attachment_path):
                    print(f"⏭️  Skipping (already processed): {os.path.basename(attachment_path)}")
                    skipped_count += 1
                    continue
                
                # Process new file
                success = self.process_file(attachment_path, email_obj)
                if success:
                    self.file_tracker.mark_as_processed(attachment_path)
                    processed_count += 1
        
        # Final summary
        print(f"\n{'='*60}")
        print(f"✅ Execution complete!")
        print(f"   Processed: {processed_count} file(s)")
        print(f"   Skipped: {skipped_count} file(s) (already processed)")
        print(f"{'='*60}\n")

    def process_file(self, filepath: str, email_metadata):
        print(f"📄 Processing: {os.path.basename(filepath)}")
        
        # 1. Parse PDF
        parsed_data = self.parser.extract_content(filepath)
        if not parsed_data:
            print("❌ Failed to extract content.")
            return False

        # 2. Extract Transactions
        transactions = self.extractor.extract_transactions(parsed_data)
        print(f"   Extracted {len(transactions)} transactions.")

        # 3. Categorize
        total_income = 0.0
        total_expense = 0.0
        
        for t in transactions:
            t.category = self.categorizer.categorize(t.description, t.amount)
            if t.type == 'ingreso':
                total_income += t.amount
            else:
                total_expense += t.amount
        
        # 4. Create Statement
        stmt = Statement(
            period=str(date.today()), # Could be extracted from PDF text
            transactions=transactions,
            total_income=total_income,
            total_expense=total_expense
        )
        
        # 5. Output JSON
        self.save_output(stmt, filepath)
        
        # 5.1 Output CSV for easy validation
        self.save_csv(stmt, filepath)
        
        # 6. Generate consolidated report
        print("\n" + "="*60)
        self.report_generator.generate_consolidated_report()
        print("="*60 + "\n")
        
        return True

    def save_output(self, statement: Statement, source_filepath: str):
        # Convert to dict for JSON
        data = {
            "period": statement.period,
            "summary": {
                "total_income": statement.total_income,
                "total_expense": statement.total_expense
            },
            "transactions": [
                {
                    "date": str(t.date),
                    "description": t.description,
                    "amount": t.amount,
                    "type": t.type,
                    "category": t.category
                }
                for t in statement.transactions
            ]
        }
        
        base_name = os.path.basename(source_filepath)
        json_name = f"{os.path.splitext(base_name)[0]}_processed.json"
        output_path = os.path.join("outputs", json_name)
        
        if not os.path.exists("outputs"):
            os.makedirs("outputs")
            
        with open(output_path, "w", encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
            
        print(f"Output saved to: {output_path}")
    
    def save_csv(self, statement: Statement, source_filepath: str):
        """Save transactions as CSV for easy validation in Excel."""
        import csv
        
        base_name = os.path.basename(source_filepath)
        csv_name = f"{os.path.splitext(base_name)[0]}_transactions.csv"
        output_path = os.path.join("outputs", csv_name)
        
        if not os.path.exists("outputs"):
            os.makedirs("outputs")
        
        with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow(['Fecha', 'Descripción', 'Monto', 'Tipo', 'Categoría'])
            
            # Write transactions
            for t in statement.transactions:
                writer.writerow([
                    str(t.date),
                    t.description,
                    f"{t.amount:,.2f}",
                    t.type.upper(),
                    t.category
                ])
            
            # Write summary
            writer.writerow([])  # Empty row
            writer.writerow(['RESUMEN'])
            writer.writerow(['Total Ingresos', f"{statement.total_income:,.2f}"])
            writer.writerow(['Total Egresos', f"{statement.total_expense:,.2f}"])
            writer.writerow(['Balance', f"{statement.total_income - statement.total_expense:,.2f}"])
        
        print(f"CSV saved to: {output_path}")

if __name__ == "__main__":
    bot = FinancialBot()
    try:
        bot.run()
    except KeyboardInterrupt:
        print("\nStopping bot...")
