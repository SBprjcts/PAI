from expense import Expense

class User:
    def __init__(self, id: int, company: str, email: str, password: str, expense_ids:list[Expense] = []) -> None:
        self.id = id
        self.company = company
        self.email = email
        self.password = password
        self.expense_ids = expense_ids
