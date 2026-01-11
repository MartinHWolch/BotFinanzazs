from config import CATEGORIES

class Categorizer:
    @staticmethod
    def categorize(description: str, amount: float = 0) -> str:
        """
        Clasifica una transacción basada en su descripción.
        Ignora mayúsculas/minúsculas.
        """
        desc_lower = description.lower()
        
        # Simple keyword matching
        for category, keywords in CATEGORIES.items():
            for keyword in keywords:
                if keyword in desc_lower:
                    return category
        
        return "Otros"
