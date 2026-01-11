from dataclasses import dataclass
from typing import List, Optional
from datetime import date

@dataclass
class Transaction:
    date: date
    description: str
    amount: float
    type: str  # 'income' or 'expense'
    category: str = "Otros"

@dataclass
class Statement:
    period: str
    transactions: List[Transaction]
    total_income: float
    total_expense: float

@dataclass
class Email:
    subject: str
    sender: str
    date: str
    attachments: List[str]  # Paths to downloaded files
