from Models.expense import Expense

class User:
    def __init__(self, company: str, email: str, password: str, id: int = 0) -> None:
        self.id = id
        self.company = company
        self.email = email
        self.password = password

    def __str__(self):
        return f"id: {self.id}\ncompany: {self.company}\nemail: {self.company}\npassword: {self.password}"