from flask import Flask, render_template, request, redirect, url_for, flash
from model import db, Expense
from datetime import datetime, date
import os
import json
from collections import defaultdict

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY','dev-secret-key-change')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expenses.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Create tables at startup (Flask 3.x compatible)
with app.app_context():
    db.create_all()


@app.route('/')
def index():
    expenses = Expense.query.order_by(Expense.date.desc()).all()
    total = sum(e.amount for e in expenses)
    return render_template('home.html', expenses=expenses, total=total)

@app.route('/add', methods=['GET','POST'])
def add_expense():
    if request.method == 'POST':
        category = request.form.get('category', 'Other')

        # amount validation
        try:
            amount = float(request.form.get('amount', '0'))
        except ValueError:
            flash('Enter a valid amount', 'danger')
            return redirect(url_for('add_expense'))

        description = request.form.get('description', '')

        # Take date from form and convert to datetime.date
        date_str = request.form.get('date')
        if date_str:
            try:
                expense_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                flash('Invalid date format. Please use YYYY-MM-DD.', 'danger')
                return redirect(url_for('add_expense'))
        else:
            expense_date = date.today()  # fallback if empty

        # Create expense
        exp = Expense(category=category, amount=amount, description=description, date=expense_date)
        db.session.add(exp)
        db.session.commit()

        flash('Expense added', 'success')
        return redirect(url_for('index'))
    return render_template('add_expense.html')


@app.route('/set_budget', methods=['GET','POST'])
def set_budget():
    remaining = None
    budget = None
    if request.method == 'POST':
        try:
            budget = float(request.form.get('budget', '0'))
        except ValueError:
            flash('Enter a valid budget','danger')
            return redirect(url_for('set_budget'))
        expenses = Expense.query.all()
        total = sum(e.amount for e in expenses)
        remaining = budget - total
        return render_template('budget.html', budget=budget, remaining=remaining)
    return render_template('budget.html', budget=budget, remaining=remaining)


@app.route('/insights')
def insights():
    expenses = Expense.query.all()

    # --- Daily expenses (for line chart) ---
    daily_data = defaultdict(float)
    for exp in expenses:
        date_str = exp.date.strftime("%Y-%m-%d")  # assuming exp.date is a datetime
        daily_data[date_str] += exp.amount

    # Sort by date
    daily_labels = sorted(daily_data.keys())
    daily_values = [daily_data[d] for d in daily_labels]

    # --- Monthly expenses (for bar chart) ---
    monthly_data = defaultdict(float)
    for exp in expenses:
        month_str = exp.date.strftime("%Y-%m")  # e.g. "2025-09"
        monthly_data[month_str] += exp.amount

    # Sort by month
    monthly_labels = sorted(monthly_data.keys())
    monthly_values = [monthly_data[m] for m in monthly_labels]

    return render_template(
        'insights.html',
        daily_labels=json.dumps(daily_labels),
        daily_values=json.dumps(daily_values),
        monthly_labels=json.dumps(monthly_labels),
        monthly_values=json.dumps(monthly_values)
    )


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
