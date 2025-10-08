from datetime import date

class Expense:
    def __init__(self, id: int, date: date, amount: float, vendor: str, description: str, category: str, anomaly_score: float):
        self.id = id
        self.date = date
        self.amount = amount
        self.vendor = vendor
        self.description = description
        self.category = category
        self.anomaly_score = anomaly_score
        