from flask import Flask, render_template, request, jsonify
from models import db, SavingCategory, SavingsTarget, Savings
from flask_migrate import Migrate
import os
from datetime import datetime

app = Flask(__name__)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///savings.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)

tables_created = False

@app.before_request
def create_tables():
    global tables_created
    if not tables_created:
        db.create_all()
        tables_created = True

@app.route('/')
def index():
    return render_template('savings.html')

@app.route('/add_saving_target', methods=['POST'])
def add_saving_target():
    data = request.json
    category = SavingCategory.query.filter_by(saving_category_name=data['saving_category_name']).first()
    if not category:
        category = SavingCategory(
            saving_category_name=data['saving_category_name'],
            saving_category_description=data['saving_category_description']
        )
        db.session.add(category)
        db.session.commit()

    target = SavingsTarget(
        user_id=1,
        saving_category_id=category.saving_category_id,
        savings_goal_name=data['savings_goal_name'],
        savings_target_amount=data['savings_target_amount'],
        savings_target_date=datetime.strptime(data['savings_target_date'], '%Y-%m-%d').date()
    )
    db.session.add(target)
    db.session.commit()

    # Create an entry in the savings table with the savings_target_id and goal name, and other details set to default values
    savings = Savings(
        user_id=2,
        savings_target_id=target.savings_target_id
    )
    db.session.add(savings)
    db.session.commit()

    return jsonify({"message": "Saving target and initial savings entry added successfully"}), 201

@app.route('/update_saving_target/<int:id>', methods=['PUT'])
def update_saving_target(id):
    data = request.json
    target = SavingsTarget.query.get(id)
    if target:
        category = SavingCategory.query.filter_by(saving_category_name=data['saving_category_name']).first()
        if not category:
            category = SavingCategory(
                saving_category_name=data['saving_category_name'],
                saving_category_description=data['saving_category_description']
            )
            db.session.add(category)
            db.session.commit()
        target.saving_category_id = category.saving_category_id
        target.savings_goal_name = data['savings_goal_name']
        target.savings_target_amount = data['savings_target_amount']
        target.savings_target_date = datetime.strptime(data['savings_target_date'], '%Y-%m-%d').date()
        db.session.commit()
        return jsonify({"message": "Saving target updated successfully"}), 200
    return jsonify({"message": "Saving target not found"}), 404

@app.route('/delete_saving_target/<int:id>', methods=['DELETE'])
def delete_saving_target(id):
    target = SavingsTarget.query.get(id)
    if target:
        savings = Savings.query.filter_by(savings_target_id=id).all()
        for saving in savings:
            db.session.delete(saving)
        db.session.delete(target)
        db.session.commit()
        return jsonify({"message": "Saving target and corresponding savings deleted successfully"}), 200
    return jsonify({"message": "Saving target not found"}), 404

@app.route('/add_savings', methods=['POST'])
def add_savings():
    data = request.json
    savings = Savings.query.filter_by(savings_target_id=data['savings_target_id']).first()
    if savings:
        savings.savings_amount_saved = data['savings_amount_saved']
        savings.savings_payment_mode = data['savings_payment_mode']
        savings.savings_date_saved = datetime.strptime(data['savings_date_saved'], '%Y-%m-%d').date()
        db.session.commit()
        return jsonify({"message": "Savings updated successfully"}), 200
    return jsonify({"message": "Savings not found"}), 404

@app.route('/get_savings/<int:id>', methods=['GET'])
def get_savings(id):
    savings = Savings.query.filter_by(savings_target_id=id).first()
    if savings:
        return jsonify({"savings": {
            "savings_target_id": savings.savings_target_id,
            "savings_goal_name": savings.savings_target.savings_goal_name,
            "savings_amount_saved": float(savings.savings_amount_saved),
            "savings_payment_mode": savings.savings_payment_mode,
            "savings_date_saved": str(savings.savings_date_saved)
        }}), 200
    target = SavingsTarget.query.get(id)
    if target:
        return jsonify({"savings": {
            "savings_target_id": target.savings_target_id,
            "savings_goal_name": target.savings_goal_name,
            "savings_amount_saved": 0,
            "savings_payment_mode": '',
            "savings_date_saved": str(datetime.today().date())
        }}), 200
    return jsonify({"savings": None}), 200

@app.route('/update_savings/<int:id>', methods=['PUT'])
def update_savings(id):
    data = request.json
    savings = Savings.query.filter_by(savings_target_id=id).first()
    if savings:
        savings.savings_amount_saved = data['savings_amount_saved']
        savings.savings_payment_mode = data['savings_payment_mode']
        savings.savings_date_saved = datetime.strptime(data['savings_date_saved'], '%Y-%m-%d').date()
        db.session.commit()
        return jsonify({"message": "Savings updated successfully"}), 200
    return jsonify({"message": "Savings not found"}), 404

@app.route('/delete_savings/<int:id>', methods=['DELETE'])
def delete_savings(id):
    savings = Savings.query.get(id)
    if savings:
        db.session.delete(savings)
        db.session.commit()
        return jsonify({"message": "Savings deleted successfully"}), 200
    return jsonify({"message": "Savings not found"}), 404

@app.route('/get_all_data', methods=['GET'])
def get_all_data():
    targets = SavingsTarget.query.all()
    data = []
    for target in targets:
        savings = Savings.query.filter_by(savings_target_id=target.savings_target_id).first()
        category = SavingCategory.query.get(target.saving_category_id)
        data.append({
            "savings_target_id": target.savings_target_id,
            "saving_category_name": category.saving_category_name,
            "saving_category_description": category.saving_category_description,
            "savings_goal_name": target.savings_goal_name,
            "savings_target_amount": float(target.savings_target_amount),
            "savings_target_date": str(target.savings_target_date),
            "savings_amount_saved": float(savings.savings_amount_saved) if savings else 0,
            "savings_payment_mode": savings.savings_payment_mode if savings else '',
            "savings_date_saved": str(savings.savings_date_saved) if savings else str(datetime.today().date()),
            "savings_updated_date": str(savings.savings_created_on) if savings else None
        })
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)
