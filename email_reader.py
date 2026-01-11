import imaplib
import email
import os
import time
from email.header import decode_header
from typing import List, Optional
from config import EMAIL_HOST, EMAIL_USER, EMAIL_PASS, SAVE_DIR
from models import Email

class EmailReader:
    def __init__(self):
        self.host = EMAIL_HOST
        self.user = EMAIL_USER
        self.password = EMAIL_PASS
        self.save_dir = SAVE_DIR
        self.connection = None

        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)

    def connect(self):
        """Establishes connection to the IMAP server."""
        try:
            self.connection = imaplib.IMAP4_SSL(self.host)
            self.connection.login(self.user, self.password)
            print(f"Connected to {self.host} as {self.user}")
        except Exception as e:
            print(f"Error connecting to email: {e}")
            raise

    def disconnect(self):
        """Closes the connection."""
        if self.connection:
            try:
                self.connection.close()
            except:
                pass
            self.connection.logout()
            print("Disconnected from email.")

    def fetch_unread_emails(self) -> List[Email]:
        """Fetches unread emails with PDF attachments."""
        if not self.connection:
            self.connect()

        self.connection.select("INBOX")
        
        # Hybrid approach: Filter by FROM on server (ASCII-safe), by SUBJECT in Python (has accent)
        from config import ALLOWED_SENDERS
        
        # Build IMAP search with FROM filters (ALL emails, not just UNSEEN)
        # Add date filter for year 2025: SINCE 1-Jan-2025 BEFORE 1-Jan-2026
        date_filter = 'SINCE "1-Jan-2025" BEFORE "1-Jan-2026"'
        
        # For 2 senders: OR FROM "sender1" FROM "sender2"
        if len(ALLOWED_SENDERS) == 1:
            search_query = f'{date_filter} FROM "{ALLOWED_SENDERS[0]}"'
        elif len(ALLOWED_SENDERS) == 2:
            search_query = f'{date_filter} OR FROM "{ALLOWED_SENDERS[0]}" FROM "{ALLOWED_SENDERS[1]}"'
        else:
            # For 3+ senders, build nested OR: OR FROM "A" OR FROM "B" FROM "C"
            from_parts = [f'FROM "{s}"' for s in ALLOWED_SENDERS]
            # Build right-to-left: OR first_sender OR second_sender third_sender
            result = from_parts[-1]
            for i in range(len(from_parts) - 2, -1, -1):
                result = f'OR {from_parts[i]} {result}'
            search_query = f'{date_filter} {result}'
        
        print(f"IMAP Search: {search_query}")
        status, messages = self.connection.search(None, search_query)
        
        email_ids = messages[0].split()
        if not email_ids:
            return []

        print(f"Found {len(email_ids)} emails from allowed senders, filtering by subject...")
        processed_emails = []

        for e_id in email_ids:
            try:
                # Fetch the email body
                res, msg_data = self.connection.fetch(e_id, "(RFC822)")
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        
                        subject, encoding = decode_header(msg["Subject"])[0]
                        if isinstance(subject, bytes):
                            subject = subject.decode(encoding if encoding else "utf-8")
                        
                        sender = msg.get("From")
                        date = msg.get("Date")

                        # Filter by subject only (sender already filtered by IMAP)
                        from config import TARGET_SUBJECT
                        
                        # Check Subject (case insensitive)
                        is_valid_subject = TARGET_SUBJECT.lower() in subject.lower()

                        if not is_valid_subject:
                            print(f"  ⏭️  Skipping: '{subject}'")
                            continue
                        
                        print(f"  ✓ Match: '{subject}'")
                        
                        # Process attachments
                        
                        # Process attachments
                        saved_files = self._save_attachments(msg)
                        
                        if saved_files:
                            processed_emails.append(Email(
                                subject=subject,
                                sender=sender,
                                date=date,
                                attachments=saved_files
                            ))
            except Exception as e:
                print(f"Error processing email {e_id}: {e}")

        return processed_emails

    def _save_attachments(self, msg) -> List[str]:
        """Saves PDF attachments from an email message."""
        saved_paths = []
        for part in msg.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get("Content-Disposition") is None:
                continue

            filename = part.get_filename()
            if filename:
                # Decode filename if needed
                filename, encoding = decode_header(filename)[0]
                if isinstance(filename, bytes):
                    filename = filename.decode(encoding if encoding else 'utf-8')

                if filename.lower().endswith(".pdf"):
                    filepath = os.path.join(self.save_dir, filename)
                    # Handle duplicate filenames
                    counter = 1
                    base, ext = os.path.splitext(filepath)
                    while os.path.exists(filepath):
                        filepath = f"{base}_{counter}{ext}"
                        counter += 1
                        
                    with open(filepath, "wb") as f:
                        f.write(part.get_payload(decode=True))
                    
                    saved_paths.append(filepath)
                    print(f"Saved attachment: {filepath}")
        
        return saved_paths

    def check_loop(self, interval=60):
        """Generator that yields new emails periodically."""
        while True:
            try:
                emails = self.fetch_unread_emails()
                if emails:
                    yield emails
            except Exception as e:
                print(f"Error in check loop: {e}")
                # Try to reconnect
                try:
                    self.disconnect()
                except:
                    pass
                self.connection = None
            
            time.sleep(interval)
