from flask_sqlalchemy import SQLAlchemy
from datetime import date

db = SQLAlchemy()

class Expense(db.Model):
    __tablename__ = "expenses"

    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)  # expense category
    amount = db.Column(db.Float, nullable=False)  # expense amount
    description = db.Column(db.String(200), nullable=True)  # optional description
    date = db.Column(db.Date, nullable=False, default=date.today)  # stores as DATE type

    def __repr__(self):
        return f"<Expense {self.id} - {self.amount} on {self.date}>"
