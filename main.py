import os
import pdfplumber
from email_reader import EmailReader
from file_tracker import FileTracker
from config import PDF_PASSWORD
from process_pdfs import procesar_todos_los_pdfs
from generate_reports import ConsolidatedReports

class FinancialBot:
    """Bot que descarga PDFs de emails, los procesa con IA y genera reportes."""
    
    def __init__(self):
        self.reader = EmailReader()
        self.file_tracker = FileTracker()
        self.pdf_password = PDF_PASSWORD

    def run(self):
        """Descarga PDFs, verifica desencriptado, procesa con IA y genera reportes."""
        print("🤖 Financial Bot - Complete Workflow")
        print(f"📂 Previously processed: {self.file_tracker.get_stats()['total_processed']} file(s)\n")
        
        # Fetch matching emails
        emails = self.reader.fetch_unread_emails()
        
        if not emails:
            print("✅ No emails found matching criteria.")
            return
        
        print(f"📧 Found {len(emails)} email(s) to process.\n")
        
        downloaded_count = 0
        skipped_count = 0
        
        for email_obj in emails:
            print(f"\n{'='*60}")
            print(f"📧 Email: {email_obj.subject}")
            print(f"   From: {email_obj.sender}")
            print(f"   Date: {email_obj.date}")
            print(f"{'='*60}")
            
            for attachment_path in email_obj.attachments:
                # Check if already processed
                if self.file_tracker.is_processed(attachment_path):
                    print(f"⏭️  Skipping: {os.path.basename(attachment_path)} (already processed)")
                    skipped_count += 1
                    continue
                
                # Verify PDF can be decrypted
                if self.verify_pdf(attachment_path):
                    self.file_tracker.mark_as_processed(attachment_path)
                    downloaded_count += 1
                    print(f"✅ Successfully downloaded and verified: {os.path.basename(attachment_path)}")
                else:
                    print(f"❌ Failed to verify: {os.path.basename(attachment_path)}")
        
        # Summary of downloads
        print(f"\n{'='*60}")
        print(f"✅ Download complete!")
        print(f"   Downloaded & verified: {downloaded_count} file(s)")
        print(f"   Skipped (duplicates): {skipped_count} file(s)")
        print(f"   Location: downloads/")
        print(f"{'='*60}\n")
        
        # Process PDFs with AI if any were downloaded
        if downloaded_count > 0:
            print("\n🤖 Iniciando procesamiento con IA...\n")
            procesar_todos_los_pdfs(input_dir="downloads", output_dir="outputs")
            
            # Generate consolidated reports
            print("\n📊 Generando reportes consolidados...\n")
            reports = ConsolidatedReports()
            reports.generate_all_reports()
        else:
            print("\n💡 No hay PDFs nuevos para procesar.\n")

    def verify_pdf(self, filepath: str) -> bool:
        """Verify that PDF can be opened and decrypted."""
        try:
            with pdfplumber.open(filepath, password=self.pdf_password) as pdf:
                # Try to access first page to verify decryption works
                if len(pdf.pages) > 0:
                    _ = pdf.pages[0]
                    print(f"   🔓 Decrypted successfully ({len(pdf.pages)} page(s))")
                    return True
                else:
                    print(f"   ⚠️  PDF has no pages")
                    return False
        except Exception as e:
            print(f"   ❌ Error: {e}")
            if "Password" in str(e):
                print(f"   💡 Hint: Check PDF_PASSWORD in .env")
            return False

if __name__ == "__main__":
    bot = FinancialBot()
    try:
        bot.run()
    except KeyboardInterrupt:
        print("\n⏹️  Stopped by user")
