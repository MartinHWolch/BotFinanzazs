import os
from dotenv import load_dotenv

load_dotenv()

# Email Configuration
EMAIL_HOST = os.getenv("EMAIL_HOST", "imap.gmail.com")
EMAIL_USER = os.getenv("EMAIL_USER", "")
EMAIL_PASS = os.getenv("EMAIL_PASS", "")
PDF_PASSWORD = os.getenv("PDF_PASSWORD", "")  # Password for PDF decryption
SAVE_DIR = os.getenv("SAVE_DIR", "./downloads")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# Email Filters
#ALLOWED_SENDERS = ["notificaciones@bancochile.cl", "enviodigital@bancochile.cl"]
ALLOWED_SENDERS = ["enviodigital@bancochile.cl"]

TARGET_SUBJECT = "Cartola Cuenta Corriente"

# Date Range Configuration (cambiar según necesidad)
# Formato: "DD-MMM-YYYY" ejemplo: "1-Jan-2025"
DATE_START = os.getenv("DATE_START", "1-Jan-2025")  # Fecha inicio para buscar emails
DATE_END = os.getenv("DATE_END", "31-Dec-2025")      # Fecha fin para buscar emails

# Report Date Range (opcional, None = incluir todas las transacciones)
REPORT_START_DATE = None  # Ejemplo: "2025-01-01" para filtrar reportes desde enero
REPORT_END_DATE = None    # Ejemplo: "2025-12-31" para filtrar reportes hasta diciembre
    