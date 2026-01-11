import os
from dotenv import load_dotenv

load_dotenv()

# Email Configuration
EMAIL_HOST = os.getenv("EMAIL_HOST", "imap.gmail.com")
EMAIL_USER = os.getenv("EMAIL_USER", "")
EMAIL_PASS = os.getenv("EMAIL_PASS", "")
PDF_PASSWORD = os.getenv("PDF_PASSWORD", "")  # Password for PDF decryption
SAVE_DIR = os.getenv("SAVE_DIR", "./downloads")

# Email Filters
#ALLOWED_SENDERS = ["notificaciones@bancochile.cl", "enviodigital@bancochile.cl"]
ALLOWED_SENDERS = ["enviodigital@bancochile.cl"]

TARGET_SUBJECT = "Cartola Cuenta Corriente"

# Categorías y keywords por defecto
CATEGORIES = {
    "Alimentación": ["supermercado", "mercado", "comida", "market", "fruteria"],
    "Transporte": ["uber", "cabify", "gasolinera", "peaje", "metro", "bus"],
    "Vivienda": ["alquiler", "hipoteca", "mantenimiento", "luz", "agua", "gas"],
    "Servicios básicos": ["internet", "telefono", "claro", "movistar", "entel"],
    "Salud": ["farmacia", "medico", "hospital", "clinica", "doctor"],
    "Educación": ["universidad", "curso", "colegio", "udemy", "platzi"],
    "Entretenimiento": ["cine", "netflix", "spotify", "juego", "steam"],
    "Compras": ["amazon", "mercadolibre", "falabella", "ripley", "zara"],
    "Suscripciones": ["prime", "hbo", "disney", "apple"],
    "Restaurantes": ["restaurante", "dominos", "starbucks", "mcdonalds", "burger"],
    "Transferencias": ["transferencia", "traspaso"],
    "Impuestos y comisiones": ["comision", "impuesto", "iva", "interes"],
    "Ingresos": ["sueldo", "salario", "deposito", "abono"],
    "Otros": []
}
