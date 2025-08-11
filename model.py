# kept for backward-compat; current app uses internal generate_insights()
def get_insights(expenses):
    if not expenses:
        return ['No expenses yet to analyze.']
    totals = {}
    total = 0
    for e in expenses:
        totals.setdefault(e.category, 0)
        totals[e.category] += float(e.amount)
        total += float(e.amount)
    top = max(totals.items(), key=lambda x: x[1])
    percent = (top[1]/total)*100 if total else 0
    tips = [f'You spent most on {top[0]} ({percent:.1f}% of total).']
    if percent > 40:
        tips.append(f'Consider reducing {top[0]} expenses.')
    return tips
