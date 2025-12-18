from datetime import date

class Expense:
    def __init__(self, user_id: int, expense_date: date, amount: float, vendor: str, description: str, category: str, anomaly_score: float, id: int = 0):
        self.id = id
        self.user_id = user_id
        self.expense_date = expense_date
        self.amount = amount
        self.vendor = vendor
        self.description = description
        self.category = category
        self.anomaly_score = anomaly_score
        