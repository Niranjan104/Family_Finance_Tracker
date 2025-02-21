from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = "uploads"

from models import db, Expense, Category

with app.app_context():
    db.init_app(app)
    db.create_all()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/get_categories")
def get_categories():
    categories = Category.query.all()
    return jsonify([{"name": cat.name, "description": cat.category_desc} for cat in categories])

@app.route("/get_expense/<int:expense_id>")
def get_expense(expense_id):
    expense = Expense.query.get(expense_id)
    if not expense:
        return jsonify({"message": "Expense not found"}), 404

    return jsonify({
        "id": expense.id,
        "name": expense.name,
        "category": expense.category.name,
        "category_desc": expense.category.category_desc,
        "date": expense.date.strftime("%Y-%m-%d"),
        "amount": expense.amount,
        "description": expense.description,
        "image": expense.image
    })

@app.route("/add_expense", methods=["POST"])
def add_expense():
    data = request.form.to_dict()
    print("Received data:", data)  # Debugging statement

    name = data.get("name")
    category_name = data.get("category")
    category_desc = data.get("category-desc", "")
    date_str = data.get("date")
    amount = data.get("amount")
    description = data.get("description", "")
    file_name = None

    if not name or not category_name or not date_str or not amount:
        print("Missing required fields!")  # Debugging statement
        return jsonify({"message": "Missing required fields!"}), 400

    try:
        amount = float(amount)
    except ValueError:
        print("Invalid amount!")  # Debugging statement
        return jsonify({"message": "Invalid amount!"}), 400

    try:
        date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        print("Invalid date format!")  # Debugging statement
        return jsonify({"message": "Invalid date format!"}), 400

    category = Category.query.filter_by(name=category_name).first()
    if not category:
        category = Category(name=category_name, category_desc=category_desc)
        db.session.add(category)
        db.session.commit()

    file = request.files.get("file-upload")
    if file and file.filename:
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(file_path)
        file_name = file.filename

    new_expense = Expense(name=name, category_id=category.category_id, date=date, amount=amount, description=description, image=file_name)
    db.session.add(new_expense)
    db.session.commit()

    print("Expense added:", new_expense)  # Debugging statement
    return jsonify({"message": "Expense added successfully!"})

@app.route("/get_expenses")
def get_expenses():
    expenses = Expense.query.all()
    return jsonify([{
        "id": exp.id, "name": exp.name, "category": exp.category.name, "date": exp.date,
        "amount": exp.amount, "description": exp.description, "image": exp.image
    } for exp in expenses])

@app.route("/edit_expense/<int:expense_id>", methods=["PUT"])
def edit_expense(expense_id):
    expense = Expense.query.get(expense_id)

    if not expense:
        return jsonify({"message": "Expense not found"}), 404

    data = request.form.to_dict()

    expense.name = data.get("name", expense.name)
    category_name = data.get("category", expense.category.name)
    category_desc = data.get("category-desc", "")
    date_str = data.get("date")
    expense.amount = float(data.get("amount", expense.amount))
    expense.description = data.get("description", expense.description)

    try:
        expense.date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"message": "Invalid date format!"}), 400

    category = Category.query.filter_by(name=category_name).first()
    if not category:
        category = Category(name=category_name, category_desc=category_desc)
        db.session.add(category)
        db.session.commit()
    expense.category_id = category.category_id

    file = request.files.get("file-upload")
    if file and file.filename:
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(file_path)
        expense.image = file.filename

    db.session.commit()

    return jsonify({"message": "Expense updated successfully!"})

@app.route("/delete_expense/<int:expense_id>", methods=["DELETE"])
def delete_expense(expense_id):
    expense = Expense.query.get(expense_id)

    if not expense:
        return jsonify({"message": "Expense not found"}), 404

    db.session.delete(expense)
    db.session.commit()

    return jsonify({"message": "Expense deleted successfully!"})

if __name__ == "__main__":
    app.run(debug=True)
