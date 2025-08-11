from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY','dev-secret-key-change')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expenses.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(80), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(300))
    date = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Expense {self.id} {self.category} {self.amount}>'

# Create tables at startup (Flask 3.x compatible)
with app.app_context():
    db.create_all()

def generate_insights(expenses):
    # simple analytics (no sklearn dependency required for basic insights)
    if not expenses:
        return ['No expenses yet to analyze.']
    from collections import defaultdict
    totals = defaultdict(float)
    total_all = 0.0
    for e in expenses:
        totals[e.category] += float(e.amount)
        total_all += float(e.amount)
    # find top category
    top_cat = max(totals.items(), key=lambda x: x[1])
    percent = (top_cat[1] / total_all) * 100 if total_all else 0
    tips = [f"You spent the most on {top_cat[0]} — ₹{top_cat[1]:.2f} ({percent:.1f}% of total)." ]
    if percent > 40:
        tips.append(f"Consider reducing {top_cat[0]} expenses or set a sub-budget for it.")
    return tips

@app.route('/')
def index():
    expenses = Expense.query.order_by(Expense.date.desc()).all()
    total = sum(e.amount for e in expenses)
    return render_template('home.html', expenses=expenses, total=total)

@app.route('/add', methods=['GET','POST'])
def add_expense():
    if request.method == 'POST':
        category = request.form.get('category','Other')
        try:
            amount = float(request.form.get('amount','0'))
        except ValueError:
            flash('Enter a valid amount','danger')
            return redirect(url_for('add_expense'))
        description = request.form.get('description','')
        date = request.form.get('date') or datetime.utcnow().date().isoformat()
        exp = Expense(category=category, amount=amount, description=description, date=date)
        db.session.add(exp)
        db.session.commit()
        flash('Expense added','success')
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
    insights_text = generate_insights(expenses)
    return render_template('insights.html', insights=insights_text)

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
