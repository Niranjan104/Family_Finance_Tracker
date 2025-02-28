from flask import Flask, render_template, request, jsonify, send_file, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
from datetime import datetime, timedelta
from io import BytesIO
import re

app = Flask(__name__)
# In app.py, ensure you have proper session configuration
app.secret_key = os.urandom(24)  # Use proper secret key
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False  # True in production with HTTPS
# Enable CORS for all routes and allow credentials (cookies) if needed
# Update CORS configuration at the top of app.py
CORS(app, supports_credentials=True, origins=["http://localhost:5000", "http://your-frontend-domain.com"])
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = "uploads"

from models import db, Expense, Category, Budget

with app.app_context():
    db.init_app(app)
    db.create_all()

# Function to strip emojis from a string
def strip_emojis(text):
    emoji_pattern = re.compile(
        "[" 
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F700-\U0001F77F"  # alchemical symbols
        "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
        "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
        "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        "\U0001FA00-\U0001FA6F"  # Chess Symbols
        "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        "\U00002600-\U000026FF"  # Miscellaneous Symbols
        "\U00002700-\U000027BF"  # Dingbats
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text)

# Function to attach emojis to categories for display purposes
def attach_emojis(category_name):
    emoji_map = {
        "Food": "🍕",
        "Transport": "🚂",
        "Bills": "💸",
        "Entertainment": "🤡",
        "Shopping": "🛍️",
        "Therapy": "🩺",
        "Others": ""
    }
    for key, emoji in emoji_map.items():
        if key in category_name:
            return f"{category_name}{emoji}"
    return category_name

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/get_categories")
def get_categories():
    categories = Category.query.all()
    return jsonify([{"name": cat.name, "description": cat.category_desc} for cat in categories])

@app.route("/add_expense", methods=["POST"])
def add_expense():
    data = request.form.to_dict()

    name = data.get("name")
    category_name = data.get("category")
    date_str = data.get("date")
    amount = data.get("amount")
    description = data.get("description", "")

    if not name or not category_name or not date_str or not amount:
        return jsonify({"message": "Missing required fields!"}), 400

    try:
        amount = float(amount)
    except ValueError:
        return jsonify({"message": "Invalid amount!"}), 400

    # Handle "Others" category input
    if category_name == "Others":
        category_name = data.get("custom-category")
        if not category_name:
            return jsonify({"message": "Custom category name is required!"}), 400

    # Remove emojis for internal storage
    category_stripped = strip_emojis(category_name)
    category = Category.query.filter_by(name=category_stripped).first()
    if not category:
        category_desc = data.get("category-desc", "")
        category = Category(name=category_stripped, category_desc=category_desc)
        db.session.add(category)
        db.session.commit()

    try:
        date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"message": "Invalid date format!"}), 400

    file = request.files.get("file-upload")
    if file and file.filename:
        file_data = file.read()
        file_type = file.mimetype
        new_expense = Expense(
            name=name,
            category_id=category.category_id,
            date=date,
            amount=amount,
            description=description,
            image_data=file_data,
            file_type=file_type
        )
    else:
        new_expense = Expense(
            name=name,
            category_id=category.category_id,
            date=date,
            amount=amount,
            description=description
        )
    db.session.add(new_expense)
    db.session.commit()

    return jsonify({"message": "Expense added successfully!"})

@app.route("/get_expenses")
def get_expenses():
    from_date = request.args.get("from_date")
    to_date = request.args.get("to_date")
    query = Expense.query
    if from_date:
        query = query.filter(Expense.date >= from_date)
    if to_date:
        query = query.filter(Expense.date <= to_date)
    expenses = query.order_by(Expense.date.desc()).all()
    return jsonify([{
        "id": exp.id,
        "name": exp.name,
        "category": attach_emojis(exp.category.name) if exp.category else "Unknown",
        "date": exp.date.strftime("%Y-%m-%d"),
        "amount": exp.amount,
        "description": exp.description,
        "image_url": f"/get_file/{exp.id}" if exp.image_data else None,
        "file_type": exp.file_type
    } for exp in expenses])

@app.route("/get_expense/<int:expense_id>")
def get_expense(expense_id):
    expense = Expense.query.get(expense_id)
    if not expense:
        return jsonify({"message": "Expense not found"}), 404
    return jsonify({
        "id": expense.id,
        "name": expense.name,
        "category": attach_emojis(expense.category.name) if expense.category else "Unknown",
        "category_desc": expense.category.category_desc if expense.category else "",
        "date": expense.date.strftime("%Y-%m-%d"),
        "amount": expense.amount,
        "description": expense.description,
        "image_url": f"/get_file/{expense.id}" if expense.image_data else None,
        "file_type": expense.file_type
    })

@app.route("/get_file/<int:expense_id>")
def get_file(expense_id):
    expense = Expense.query.get(expense_id)
    if not expense or not expense.image_data:
        return jsonify({"message": "File not found"}), 404
    return send_file(BytesIO(expense.image_data), mimetype=expense.file_type)

@app.route("/edit_expense/<int:expense_id>", methods=["PUT"])
def edit_expense(expense_id):
    expense = Expense.query.get(expense_id)
    if not expense:
        return jsonify({"message": "Expense not found"}), 404
    data = request.form.to_dict()
    expense.name = data.get("name", expense.name)
    category_name = data.get("category", expense.category.name)
    try:
        expense.amount = float(data.get("amount", expense.amount))
    except ValueError:
        return jsonify({"message": "Invalid amount!"}), 400
    expense.description = data.get("description", expense.description)
    if category_name == "Others":
        category_name = data.get("custom-category")
        if not category_name:
            return jsonify({"message": "Custom category name is required!"}), 400
    category = Category.query.filter_by(name=strip_emojis(category_name)).first()
    if not category:
        category_desc = data.get("category-desc", "")
        category = Category(name=strip_emojis(category_name), category_desc=category_desc)
        db.session.add(category)
        db.session.commit()
    expense.category_id = category.category_id
    try:
        expense.date = datetime.strptime(data.get("date"), "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"message": "Invalid date format!"}), 400
    file = request.files.get("file-upload")
    if file and file.filename:
        file_data = file.read()
        expense.image_data = file_data
        expense.file_type = file.mimetype
    db.session.commit()
    return jsonify({"message": "Expense updated successfully!"})

@app.route("/delete_expense/<int:expense_id>", methods=["DELETE"])
def delete_expense(expense_id):
    expense = Expense.query.get(expense_id)
    if not expense:
        return jsonify({"message": "Expense not found"}), 404
    category_id = expense.category_id
    db.session.delete(expense)
    db.session.commit()
    # If no expense uses the category, delete the category as well
    remaining_expenses = Expense.query.filter_by(category_id=category_id).count()
    if remaining_expenses == 0:
        category = Category.query.get(category_id)
        db.session.delete(category)
        db.session.commit()
    return jsonify({"message": "Expense deleted successfully!"})

@app.route("/get_stats")
def get_stats():
    from_date = request.args.get("from_date")
    to_date = request.args.get("to_date")
    query = Expense.query
    if from_date:
        query = query.filter(Expense.date >= from_date)
    if to_date:
        query = query.filter(Expense.date <= to_date)
    total_spent = query.with_entities(db.func.sum(Expense.amount)).scalar() or 0
    expense_count = query.with_entities(db.func.count(Expense.id)).scalar() or 0
    last_7days_spent = query.with_entities(db.func.sum(Expense.amount)).filter(
        Expense.date >= (datetime.now().date() - timedelta(days=7))
    ).scalar() or 0
    highest_category = query.with_entities(
        Category.name, db.func.sum(Expense.amount)
    ).join(Category).group_by(Category.name).order_by(db.func.sum(Expense.amount).desc()).first()
    highest_amount = query.with_entities(db.func.max(Expense.amount)).scalar() or 0
    highest_category_name = attach_emojis(highest_category[0]) if highest_category else "Empty!😶"
    return jsonify({
        "total_spent": float(total_spent),
        "expense_count": expense_count,
        "last_7days_spent": float(last_7days_spent),
        "highest_category": highest_category_name,
        "highest_amount": float(highest_amount)
    })

@app.route('/set_period', methods=['POST'])
def set_period():
    try:
        data = request.get_json()
        if not data or 'year' not in data or 'month' not in data:
            return jsonify({'error': 'Missing required fields'}), 400
        year = int(data['year'])
        month = int(data['month'])
        if not (1 <= month <= 12):
            return jsonify({'error': 'Invalid month'}), 400
        if year < 2000 or year > 2100:
            return jsonify({'error': 'Invalid year'}), 400
        session['current_year'] = year
        session['current_month'] = month
        return jsonify({'message': 'Period set successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/add_budget', methods=['POST'])
def add_budget():
    try:
        data = request.get_json()
        if not data or 'category' not in data or 'amount' not in data:
            return jsonify({'error': 'Missing category or amount'}), 400
        
        # Get period from session
        year = session.get('current_year')
        month = session.get('current_month')
        if not year or not month:
            return jsonify({'error': 'Period not set'}), 400
        
        # Process category
        category_name = strip_emojis(data['category'].split(' ')[0])  # Remove emoji and any trailing space
        amount = float(data['amount'])
        
        # Find or create category
        category = Category.query.filter_by(name=category_name).first()
        if not category:
            category = Category(name=category_name)
            db.session.add(category)
            db.session.commit()

        # Create budget entry
        new_budget = Budget(
            category_id=category.category_id,
            amount=amount,
            month=month,
            year=year
        )
        
        db.session.add(new_budget)
        db.session.commit()
        
        return jsonify({'message': 'Budget saved successfully'}), 200

    except ValueError as ve:
        return jsonify({'error': f'Invalid data format: {str(ve)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
    
if __name__ == "__main__":
    app.run(debug=True)
