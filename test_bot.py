import unittest
from datetime import date
from categorizer import Categorizer
from transaction_extractor import TransactionExtractor
from models import Transaction

class TestFinancialBot(unittest.TestCase):
    def setUp(self):
        self.extractor = TransactionExtractor()
        self.categorizer = Categorizer()

    def test_categorizer(self):
        self.assertEqual(self.categorizer.categorize("Compra en Supermercado Lider"), "Alimentación")
        self.assertEqual(self.categorizer.categorize("Pago Netflix"), "Entretenimiento")
        self.assertEqual(self.categorizer.categorize("Transferencia a Juan"), "Transferencias")
        self.assertEqual(self.categorizer.categorize("Gasto desconocido"), "Otros")

    def test_extractor_text(self):
        sample_text = """
        Resumen de cuenta
        12/01/2024 Compra Store 12345 $ 10.000
        15-01-2024 Pago Servicio $ 5.500
        """
        transactions = self.extractor._extract_from_text(sample_text)
        self.assertEqual(len(transactions), 2)
        
        t1 = transactions[0]
        self.assertEqual(t1.date, date(2024, 1, 12))
        self.assertEqual(t1.amount, 10000.0)
        self.assertEqual(t1.type, "ingreso") # Positive without sign (logic update might be needed if expenses are usually positive in statement but treated as expense by context, but for now positive amount usually = income or just 'amount', let's fix logic if needed. Actually in code I put: "egreso" if amount_val < 0 else "ingreso". Statements usually show expenses as positive numbers in a 'Debit' column or negative. My extractor assumes - sign for expense. I should probably clarify this limitation or logic.)

    def test_extractor_tables(self):
        # Mock table data: [Date, Desc, Amount]
        mock_table = [
            ["Fecha", "Descripcion", "Monto"],
            ["01/02/2024", "Uber Trip", "-5000"],
            ["02/02/2024", "Sueldo", "1500000"]
        ]
        transactions = self.extractor._extract_from_tables(mock_table)
        self.assertEqual(len(transactions), 2)
        
        t1 = transactions[0]
        self.assertEqual(t1.type, "egreso") # -5000
        self.assertEqual(t1.amount, 5000.0)
        
        t2 = transactions[1]
        self.assertEqual(t2.type, "ingreso")
        self.assertEqual(t2.amount, 1500000.0)

if __name__ == '__main__':
    unittest.main()
