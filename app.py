from flask import Flask, render_template, request, redirect, url_for, flash
from model import db, Expense, Budget
from datetime import datetime, date , timedelta
import os
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
    today=date.today()
    year, month = today.year, today.month

    budget_object = Budget.query.filter_by(year=year, month=month).first()

    if request.method == 'POST':
        try:
            budget_value = float(request.form.get('budget', '0'))
        except ValueError:
            flash('Enter a valid budget','danger')
            return redirect(url_for('set_budget'))
        if budget_object:
            budget_object.amount = budget_value
        else:
            budget_object = Budget(year=year, month=month, amount=budget_value)
            db.session.add(budget_object)
        db.session.commit()
        flash('Budget set successfully','success')
        return redirect(url_for('set_budget'))
    
    # calculating remaining budget for this month

    expenses = Expense.query.filter(
        Expense.date >= date(year, month, 1),
        Expense.date <= date(year, month, calendar.monthrange(year, month)[1])
    ).all()

    total_spent = sum(e.amount for e in expenses)
    remaining = (budget_object.amount - total_spent) if budget_object else None
    return render_template('budget.html', budget=budget_object.amount if budget_object else None,remaining=remaining)


@app.route('/insights')
def insights():
    expenses = Expense.query.all()
    today = date.today()
    year, month = today.year, today.month
    budget_obj = Budget.query.filter_by(year=year, month=month).first()
    budget = budget_obj.amount if budget_obj else 0

    total_spent = sum(e.amount for e in expenses if e.date.month == month and e.date.year == year)
    remaining = (budget - total_spent) if budget else 0

    first_day = date(year, month, 1)
    days_passed = (today - first_day).days + 1  # inclusive of today
    days_in_month = calendar.monthrange(year, month)[1]

    projected = round((total_spent / days_passed) * days_in_month, 2) if days_passed else 0
    
    percent_used = round((total_spent / budget) * 100, 1) if budget else 0


    

    # ✅ Line chart → Last 30 days
    daily_summary = defaultdict(float)
    cutoff_date = today - timedelta(days=29)   # last 30 days inclusive
    for e in expenses:
        if isinstance(e.date, (datetime, date)) and e.date >= cutoff_date:
            d = e.date.strftime("%Y-%m-%d")
            daily_summary[d] += e.amount

    # Fill missing days with 0
    daily_labels = [(cutoff_date + timedelta(days=i)).strftime("%d-%m") for i in range(30)]
    #daily_values = [daily_summary[d] if d in daily_summary else 0 for d in daily_labels]
    daily_values = [
        daily_summary[(cutoff_date + timedelta(days=i)).strftime("%Y-%m-%d")]
        if (cutoff_date + timedelta(days=i)).strftime("%Y-%m-%d") in daily_summary
        else 0 
        for i in range(30) ]

    # ✅ Bar chart → Current year (Jan → current month)
    monthly_summary = defaultdict(float)
    for e in expenses:
        if isinstance(e.date, (datetime, date)) and e.date.year == today.year:
            m = e.date.month
            monthly_summary[m] += e.amount

    # Always include all months from Jan to current month
    monthly_labels = [calendar.month_abbr[m] for m in range(1, today.month + 1)]
    monthly_values = [monthly_summary[m] if m in monthly_summary else 0 for m in range(1, today.month + 1)]

    # ✅ Category-wise
    category_summary = defaultdict(float)
    for e in expenses:
        normalized_category = e.category.strip().lower()
        category_summary[normalized_category] += e.amount
    category_labels = [c.title() for c in category_summary.keys()]
    category_values = list(category_summary.values())

    if category_summary:
        top_category = max(category_summary, key=category_summary.get)
        top_category_amount = category_summary[top_category]
    else:
        top_category, top_category_amount = "N/A", 0

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


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
