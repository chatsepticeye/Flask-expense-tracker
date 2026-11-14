# from flask import Flask, render_template, request, url_for, make_response, flash, redirect
# from flask_sqlalchemy import SQLAlchemy
# from datetime import datetime, date as dt_date

# app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expenses.db'
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# app.config['SECRET_KEY'] = 'my-secret-key'
# db = SQLAlchemy(app)

# class Expense(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     title = db.Column(db.String(100), nullable=False)
#     amount = db.Column(db.Float, nullable=False)
#     category = db.Column(db.String(50), nullable=False)
#     date = db.Column(db.Date, nullable=False)

# with app.app_context():
#     db.create_all()
    
#     # Check if the database is empty, then bulk-inject multiple test items
#     if not Expense.query.first():
#         test_entries = [
#             Expense(title="Chai Break", amount=20.0, category="Food", date=dt_date.today()),
#             Expense(title="Gym Membership", amount=1500.0, category="Health", date=dt_date.today()),
#             Expense(title="Metro Recharge", amount=500.0, category="Transport", date=dt_date.today()),
#             Expense(title="Streaming Subscription", amount=199.0, category="Entertainment", date=dt_date.today()),
#             Expense(title="Football Turf Booking", amount=350.0, category="Sports", date=dt_date.today())
#         ]
        
#         # Add all rows to the current tracking session
#         db.session.add_all(test_entries)
#         db.session.commit()
#         print("Successfully loaded 5 baseline testing expenses!")

# @app.route("/")
# def index():
#     # Fetch all stored items from the database sorted by date
#     expenses = Expense.query.order_by(Expense.date.desc()).all()
    
#     # Calculate the sum total of all expense amounts smoothly
#     total = sum(exp.amount for exp in expenses)
    
#     # Pass them directly down to the index.html Jinja engine
#     return render_template("index.html", expenses=expenses, total=total)

# @app.route("/add", methods=["POST"])
# def add():
#     description = request.form.get("description").strip()
#     amount_str = request.form.get("amount").strip()
#     category = request.form.get("category").strip()
#     date_str = request.form.get("date").strip()

#     if not description or not amount_str or not category or not date_str:
#         return redirect(url_for('index'))
        
#     try:
#         amount = float(amount_str)
#         if amount <= 0:
#             raise ValueError("Amount must be positive")
#     except ValueError:
#         flash("Amount must be positive number")
#         return redirect(url_for('index'))
        
#     try:
#         d = datetime.strptime(date_str, "%Y-%m-%d").date() if date_str else dt_date.today()
#     except ValueError:
#         d = dt_date.today()

#     # Create the record, committing it cleanly to the tables
#     e = Expense(title=description, amount=amount, category=category, date=d)
#     db.session.add(e)
#     db.session.commit()
    
#     # Send the success alert string forward
#     flash('Expense added successfully!')
#     return redirect(url_for('index'))

# if __name__ == "__main__":
#     app.run(debug=True, port=5000)
   
import io
import csv
from datetime import datetime, date as dt_date
from flask import Flask, render_template, request, redirect, url_for, flash, Response
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expenses.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'my-secret-key'
db = SQLAlchemy(app)

CATEGORIES = ["Food", "Transport", "Rent", "Utilities", "Health", "Entertainment", "Sports"]

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    date = db.Column(db.Date, nullable=False)

    @property
    def description(self):
        return self.title

    @description.setter
    def description(self, value):
        self.title = value

with app.app_context():
    db.create_all()
    if not Expense.query.first():
        test_entries = [
            Expense(title="Chai Break", amount=20.0, category="Food", date=dt_date.today()),
            Expense(title="Gym Membership", amount=1500.0, category="Health", date=dt_date.today()),
            Expense(title="Metro Recharge", amount=500.0, category="Transport", date=dt_date.today()),
            Expense(title="Streaming Subscription", amount=199.0, category="Entertainment", date=dt_date.today()),
            Expense(title="Football Turf Booking", amount=350.0, category="Sports", date=dt_date.today()),
        ]
        db.session.add_all(test_entries)
        db.session.commit()

@app.route("/")
def index():
    query = Expense.query
    start_date = request.args.get("start")
    end_date = request.args.get("end")
    category = request.args.get("category")

    if start_date:
        query = query.filter(Expense.date >= dt_date.fromisoformat(start_date))
    if end_date:
        query = query.filter(Expense.date <= dt_date.fromisoformat(end_date))
    if category:
        query = query.filter(Expense.category == category)

    expenses = query.order_by(Expense.date.desc()).all()
    total = sum(e.amount for e in expenses)

    # Prepare data for Chart.js
    cat_totals = {}
    day_totals = {}
    for e in expenses:
        cat_totals[e.category] = cat_totals.get(e.category, 0) + e.amount
        day_str = e.date.strftime("%Y-%m-%d")
        day_totals[day_str] = day_totals.get(day_str, 0) + e.amount

    return render_template(
        "index.html",
        expenses=expenses,
        total=total,
        categories=CATEGORIES,
        cat_labels=list(cat_totals.keys()),
        cat_data=list(cat_totals.values()),
        day_labels=sorted(list(day_totals.keys())),
        day_data=[day_totals[d] for d in sorted(day_totals.keys())]
    )

@app.route("/add", methods=["POST"])
def add():
    desc = request.form.get("description")
    amount = request.form.get("amount")
    category = request.form.get("category")
    date_str = request.form.get("date")

    if desc and amount and category:
        entry_date = dt_date.fromisoformat(date_str) if date_str else dt_date.today()
        new_expense = Expense(
            title=desc,
            amount=float(amount),
            category=category,
            date=entry_date
        )
        db.session.add(new_expense)
        db.session.commit()
        flash("Expense added successfully!", "success")
    return redirect(url_for("index"))

@app.route("/edit/<int:expense_id>", methods=["GET"])
def edit(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    return render_template("edit.html", expense=expense, categories=CATEGORIES, today=dt_date.today().strftime('%Y-%m-%d'))

@app.route("/edit/<int:expense_id>", methods=["POST"])
def edit_post(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    expense.title = request.form.get("description")
    expense.amount = float(request.form.get("amount"))
    expense.category = request.form.get("category")
    date_str = request.form.get("date")
    if date_str:
        expense.date = dt_date.fromisoformat(date_str)

    db.session.commit()
    flash("Expense updated successfully!", "success")
    return redirect(url_for("index"))

@app.route("/delete/<int:expense_id>", methods=["POST"])
def delete(expense_id):
    expense = Expense.query.get_or_404(expense_id)
    db.session.delete(expense)
    db.session.commit()
    flash("Expense deleted!", "success")
    return redirect(url_for("index"))

@app.route("/export")
def export_csv():
    expenses = Expense.query.order_by(Expense.date.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Description", "Category", "Amount", "Date"])
    for e in expenses:
        writer.writerow([e.id, e.title, e.category, e.amount, e.date.strftime("%Y-%m-%d")])
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=expenses.csv"}
    )

if __name__ == "__main__":
    app.run(debug=True)