from flask_sqlalchemy import SQLAlchemy
from datetime import date
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password= db.Column(db.String(200), nullable=False)

    expenses = db.relationship("Expense", backref="user", lazy=True)
    budgets = db.relationship("Budget", backref="user", lazy=True)

    def __repr__(self):
        return f"<User {self.username}>"


class Expense(db.Model):
    __tablename__ = "expenses"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200), nullable=True)
    date = db.Column(db.Date, nullable=False, default=date.today)

    def __repr__(self):
        return f"<Expense {self.id} - {self.amount} on {self.date}>"


class Budget(db.Model):
    __tablename__ = "budgets"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Float, nullable=False)

    __table_args__ = (
        db.UniqueConstraint("user_id", "year", "month", name="unique_user_month_budget"),
    )

    def __repr__(self):
        return f"<Budget {self.month}-{self.year}: {self.amount}>"
