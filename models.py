from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class SavingCategory(db.Model):
    __tablename__ = 'saving_category'
    saving_category_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    saving_category_name = db.Column(db.String(255), nullable=False, unique=True)
    saving_category_description = db.Column(db.Text)
    
    saving_targets = db.relationship('SavingsTarget', backref='saving_category', lazy=True)

class SavingsTarget(db.Model):
    __tablename__ = 'savings_target'
    savings_target_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=False, default=1)
    saving_category_id = db.Column(db.Integer, db.ForeignKey('saving_category.saving_category_id'), nullable=False)
    savings_goal_name = db.Column(db.String(255), nullable=False)
    savings_target_amount = db.Column(db.Numeric(10, 2), nullable=False)
    savings_target_date = db.Column(db.Date)
    savings_target_created_on = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    savings = db.relationship('Savings', backref='savings_target', lazy=True)

class Savings(db.Model):
    __tablename__ = 'savings'
    savings_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=False, default=2)
    savings_target_id = db.Column(db.Integer, db.ForeignKey('savings_target.savings_target_id'), nullable=False)
    savings_amount_saved = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    savings_payment_mode = db.Column(db.String(50), nullable=False, default='')
    savings_date_saved = db.Column(db.Date, nullable=False, default=db.func.current_date())
    savings_created_on = db.Column(db.DateTime, default=db.func.current_timestamp())
