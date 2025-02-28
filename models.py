from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Category(db.Model):
    __tablename__ = 'category'
    category_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    category_desc = db.Column(db.String(255), nullable=True)
    
    # Relationships
    expenses = db.relationship('Expense', backref='category', lazy=True)
    budgets = db.relationship('Budget', backref='category', lazy=True)

class Expense(db.Model):
    __tablename__ = 'expense'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.category_id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    date = db.Column(db.Date, nullable=False)  # Only store the date part
    description = db.Column(db.Text)
    image_data = db.Column(db.LargeBinary)  # Store file data
    file_type = db.Column(db.String(50))    # Store the file MIME type
    created_on = db.Column(db.DateTime, default=db.func.current_timestamp())

class Budget(db.Model):
    __tablename__ = 'budget'
    budget_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.category_id'), nullable=False)
    # category_name = db.Column(db.String(255), nullable=False)  # Store the category name as well
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    recurring = db.Column(db.Boolean, default=False)
    created_on = db.Column(db.DateTime, default=db.func.current_timestamp())
