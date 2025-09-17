from flask import Flask, render_template, request, redirect, url_for, flash
from model import db, Expense
from datetime import datetime, date
import os
import json
import calendar
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
    filter_option = request.args.get("filter", "all")  # default = all
    
    if filter_option == "month":
        today = date.today()
        first_day = date(today.year, today.month, 1)
        last_day = date(today.year, today.month, calendar.monthrange(today.year, today.month)[1])
        
        expenses = Expense.query.filter(
            Expense.date >= first_day,
            Expense.date <= last_day
        ).order_by(Expense.date.desc()).all()
    else:
        expenses = Expense.query.order_by(Expense.date.desc()).all()
    
    total = sum(e.amount for e in expenses)
    return render_template(
        'home.html',
        expenses=expenses,
        total=total,
        filter_option=filter_option
    )
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
    # ✅ Fetch all expenses
    expenses = Expense.query.all()

    # ✅ Budget (you can fetch from DB if user sets it dynamically)
    budget = 20000  

    # ✅ Totals
    total_spent = sum(e.amount for e in expenses)
    remaining = budget - total_spent if budget else 0

    # ✅ Days passed in current month
    today = date.today()
    first_day = today.replace(day=1)
    days_passed = (today - first_day).days + 1
    days_in_month = 30  # or use calendar.monthrange(today.year, today.month)[1]

    # ✅ Projected spending (simple extrapolation)
    projected = round((total_spent / days_passed) * days_in_month, 2) if days_passed else 0

    # ✅ % used
    percent_used = round((total_spent / budget) * 100, 1) if budget else 0

    # ✅ Daily trend
    daily_summary = defaultdict(float)
    for e in expenses:
        d = e.date.strftime("%Y-%m-%d") if isinstance(e.date, (datetime, date)) else str(e.date)
        daily_summary[d] += e.amount
    daily_labels = list(daily_summary.keys())
    daily_values = list(daily_summary.values())

    # ✅ Monthly trend
    monthly_summary = defaultdict(float)
    for e in expenses:
        m = e.date.strftime("%b") if isinstance(e.date, (datetime, date)) else str(e.date)
        monthly_summary[m] += e.amount
    monthly_labels = list(monthly_summary.keys())
    monthly_values = list(monthly_summary.values())

    # ✅ Category-wise
    category_summary = defaultdict(float)
    for e in expenses:
        category_summary[e.category] += e.amount
    category_labels = list(category_summary.keys())
    category_values = list(category_summary.values())

    # ✅ Top category
    if category_summary:
        top_category = max(category_summary, key=category_summary.get)
        top_category_amount = category_summary[top_category]
    else:
        top_category, top_category_amount = "N/A", 0

    # ✅ Indian average spending (mock, you can load from CSV later)
    avg_indian = 15000 

    return render_template(
        'insights.html',
        budget=budget,
        total_spent=total_spent,
        remaining=remaining,
        projected=projected,
        percent_used=percent_used,
        days_passed=days_passed,
        daily_labels=daily_labels,
        daily_values=daily_values,
        monthly_labels=monthly_labels,
        monthly_values=monthly_values,
        category_labels=category_labels,
        category_values=category_values,
        top_category=top_category,
        top_category_amount=top_category_amount,
        avg_indian=avg_indian
    )
# @app.route('/insights')
# def insights():
#     expenses = Expense.query.all()

#     # --- Daily expenses (for line chart) ---
#     daily_data = defaultdict(float)
#     for exp in expenses:
#         date_str = exp.date.strftime("%Y-%m-%d")  # assuming exp.date is a datetime
#         daily_data[date_str] += exp.amount

#     # Sort by date
#     daily_labels = sorted(daily_data.keys())
#     daily_values = [daily_data[d] for d in daily_labels]

#     # --- Monthly expenses (for bar chart) ---
#     monthly_data = defaultdict(float)
#     for exp in expenses:
#         month_str = exp.date.strftime("%Y-%m")  # e.g. "2025-09"
#         monthly_data[month_str] += exp.amount

#     # Sort by month
#     monthly_labels = sorted(monthly_data.keys())
#     monthly_values = [monthly_data[m] for m in monthly_labels]

#     return render_template(
#         'insights.html',
#         daily_labels=json.dumps(daily_labels),
#         daily_values=json.dumps(daily_values),
#         monthly_labels=json.dumps(monthly_labels),
#         monthly_values=json.dumps(monthly_values)
#     )


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
