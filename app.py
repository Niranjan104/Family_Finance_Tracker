from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from functools import wraps
from flask_cors import CORS
from datetime import datetime, timedelta,timezone
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Expense, Category, Budget, User
from io import BytesIO
import random, string, os,re
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from threading import Thread

from graphs import * 

app = Flask(__name__)
app.secret_key = "unifiedfamilyfinancetracker"
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False 

# Configure database
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///ufft_database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = "uploads"

db.init_app(app)


# Configure Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'thariqali142@gmail.com'
app.config['MAIL_PASSWORD'] = 'vheo bjfy yppk tyiu'  # Use App Password
app.config['MAIL_DEFAULT_SENDER'] = 'thariqali142@gmail.com'  # Add this line
mail = Mail(app)

# Function to generate OTP
def generate_otp():
    return ''.join(random.choices(string.digits, k=6))  # 6-digit OTP

# Function to send OTP
def send_otp(email, otp):
    msg = Message("Your OTP for Unified Family Finance Tracker", sender="your_email@gmail.com", recipients=[email])
    msg.body = f"""
                Dear User,

                Your One-Time Password (OTP) for verifying your Unified Family Finance Tracker account is: {otp}

                This OTP is valid for a limited time. Please do not share it with anyone for security reasons.

                If you did not request this, please ignore this message.

                Best regards,  
                Unified Family Finance Tracker Team """
    mail.send(msg)


@app.route('/')
def home():
    return render_template('login.html')


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'email' not in session:
            flash("You must be logged in to access this page.")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        family_name = request.form['family_name']
        email = request.form['email']
        password = request.form['password']
        phone = request.form['phone']
        address = request.form['address']
        
        # Check if email already exists
        existing_user = User.query.filter((User.email == email) | (User.username == username)).first()
        if existing_user:
            flash("Email or username already exists. Please use a different email or username.", "error")
            return redirect(url_for('register'))
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, family_name=family_name, email=email, password=hashed_password, phone=phone, address=address)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    
    return render_template('register.html')

# Route for login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            if user.role == "super_user" and user.status != "approved":
                flash("Your account is pending approval. Please contact the admin.")
                return redirect(url_for('login'))
            elif user.role == "family_member" and user.status != "approved":
                flash("Your account is pending approval. Please wait for the super user to approve it.")
                return redirect(url_for('login'))

            session["user_id"] = user.id
            session["role"] = user.role
            session["email"] = email

            if user.role == "admin":
                return redirect(url_for("admin_dashboard"))

            elif user.role == "super_user" or user.role == "family_member":
                otp = generate_otp()
                session['otp'] = otp  
                send_otp(email, otp)
                return redirect(url_for('verify'))
            
        flash('Invalid email or password')
    
    return render_template('login.html')


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email'].strip()
        user = User.query.filter_by(email=email).first()

        if user:
            otp = generate_otp()
            session['reset_otp'] = otp
            session['reset_email'] = email
            session['reset_otp_expiry'] = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()

            try:
                send_otp(email, otp)
                flash('An OTP has been sent to your email.', 'success')
                return redirect(url_for('verify_reset_otp'))
            except Exception as e:
                flash(f'Failed to send OTP: {str(e)}', 'error')
                return redirect(url_for('forgot_password'))
        else:
            flash('Email not found.', 'error')
    return render_template('forgot_password.html')
    
@app.route('/verify_reset_otp', methods=['GET', 'POST'])
def verify_reset_otp():
    if 'reset_otp' not in session or 'reset_email' not in session:
        flash('Invalid request. Please try again.', 'error')
        return redirect(url_for('forgot_password'))

    if datetime.now(timezone.utc) > datetime.fromisoformat(session['reset_otp_expiry']):
        flash('OTP has expired. Please request a new OTP.', 'error')
        session.pop('reset_otp', None)
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        entered_otp = ''.join([request.form.get(f'otp{i}') for i in range(1, 7)])
        actual_otp = session.get('reset_otp')

        if entered_otp == actual_otp:
            return redirect(url_for('reset_password'))
        else:
            flash('Invalid OTP. Please try again.', 'error')
    return render_template('verify_otp.html')

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if 'reset_otp' not in session or 'reset_email' not in session:
        flash('Invalid request. Please try again.', 'error')
        return redirect(url_for('forgot_password'))

    if datetime.now(timezone.utc) > datetime.fromisoformat(session['reset_otp_expiry']):
        flash('OTP has expired. Please request a new OTP.', 'error')
        session.pop('reset_otp', None)
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('reset_password'))
        
        user = User.query.filter_by(email=session['reset_email']).first()
        if user:
            user.password = generate_password_hash(password)
            db.session.commit()

            session.pop('reset_otp', None)
            session.pop('reset_email', None)
            session.pop('reset_otp_expiry', None)

            return redirect(url_for('login'))
        else:
            flash('User not found.', 'error')
    return render_template('reset_password.html')

@app.route("/admin_dashboard")
@login_required
def admin_dashboard():
    if "user_id" not in session or session.get("role") != "admin":
        return redirect(url_for("login"))
    
    page = request.args.get('page', 1, type=int)
    users = User.query.filter_by(role="super_user").paginate(page=page, per_page=4, error_out=False)

    return render_template("admin_dashboard.html", users=users)

@app.route('/verify', methods=['GET', 'POST'])
@login_required
def verify():
    if session.get('verified'):
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        entered_otp = ''.join([request.form.get(f'otp{i}') for i in range(1, 7)])
        actual_otp = session.get('otp')

        if entered_otp == actual_otp:
            session.pop('otp', None)
            session['verified'] = True
            return redirect(url_for('dashboard'))

        flash("Invalid OTP, Please Try Again!")

    return render_template('verification.html')

@app.route('/dashboard')
@login_required
def dashboard():
    if not session.get('verified'):
        return redirect(url_for('verify'))

    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if not user:  # Check if user is None
        return redirect(url_for('login'))

    # Check and create recurring budgets for this month
    check_and_create_recurring_budgets(user.id if user.role == "super_user" else user.approved_by)

    today = datetime.today()
    default_year = today.year
    default_month = today.month
    current_year = today.year  # Add this line

    all_users = []  
    if user.role == "super_user":
        all_users.append(user.username)  
        family_members = User.query.filter(User.approved_by == user.id).order_by(User.id).all()
        all_users.extend([member.username for member in family_members]) 
    elif user.role == "family_member":
        superuser = User.query.get(user.approved_by)
        if superuser:
            all_users.append(superuser.username)  
        all_users.append(user.username)

    default_user = all_users[0] if all_users else None
    monthly_plot = generate_monthly_expenses_plot(user_id=user.id)
    category_plot = generate_category_expenses_plot(default_year, default_month, user_id=user.id)
    pie_chart = generate_pie_chart(user_id=user.id, month=default_month, year=default_year)
    bar_chart = generate_bar_chart(user_id=user.id, month=default_month, year=default_year)
    stacked_bar_chart = generate_stacked_bar_chart(user_id=user.id, month=default_month, year=default_year)
    line_chart = generate_line_chart(year=default_year, user_id=user.id)

    if user.role == "super_user":
        return render_template("dashboard_edit.html", is_super_user=True,
                               username=user.username,
                               users=all_users,
                               default_user=default_user,
                               monthly_plot=monthly_plot,
                               category_plot=category_plot,
                               pie_chart=pie_chart,
                               bar_chart=bar_chart,
                               stacked_bar_chart=stacked_bar_chart,
                               line_chart=line_chart,
                               default_year=default_year,
                               default_month=default_month,
                               current_year=current_year)  # Pass current_year

    elif user.role == "family_member" and user:
        if user.status == "approved":
            if user.privilege == "view":
                return render_template("dashboard_view.html", username=user.username,
                                       users=all_users,
                                       default_user=default_user,
                                       monthly_plot=monthly_plot,
                                       category_plot=category_plot,
                                       pie_chart=pie_chart,
                                       bar_chart=bar_chart,
                                       stacked_bar_chart=stacked_bar_chart,
                                       line_chart=line_chart,
                                       default_year=default_year,
                                       default_month=default_month,
                                       current_year=current_year)  # Pass current_year

            elif user.privilege == "edit":
                return render_template("dashboard_edit.html", username=user.username,
                                       users=all_users,
                                       default_user=default_user,
                                       monthly_plot=monthly_plot,
                                       category_plot=category_plot,
                                       pie_chart=pie_chart,
                                       bar_chart=bar_chart,
                                       stacked_bar_chart=stacked_bar_chart,
                                       line_chart=line_chart,
                                       default_year=default_year,
                                       default_month=default_month,
                                       current_year=current_year)  # Pass current_year

            flash("Your account is pending approval.", "warning")
            return redirect(url_for("login"))


@app.route("/update_approved_by", methods=["POST"])
def update_approved_by():
    user_id = request.form.get("user_id")
    approve = request.form.get("approve")  
    admin_id = session.get("user_id")

    user = User.query.get(user_id)

    if not user:
        flash("User not found.", "error")
        return redirect(url_for("admin_dashboard"))

    if approve:
        user.approved_by = admin_id
        user.status = "approved"
        flash(f"User {user.username} has been approved.", "success")
    else:
        user.approved_by = None
        user.status = "pending"

        # **Check if the user is a super user**
        family_members = User.query.filter_by(approved_by=user.id).all()
        
        if family_members:
            for member in family_members:
                member.status = "pending"
            
            flash(f"Super user {user.username} and all family members have been disapproved.", "warning")
        else:
            flash(f"User {user.username} has been disapproved.", "warning")

    db.session.commit()

    return redirect(url_for("admin_dashboard"))


@app.route("/super_user_dashboard")
@login_required
def super_user_dashboard():
    if "user_id" not in session or session["role"] != "super_user":
        return redirect(url_for("login"))
    family_members = User.query.filter_by(approved_by=session["user_id"]).all()
    return render_template("super_user_dash.html",family_members=family_members)


@app.route("/create_subaccount", methods=["POST"])
def create_subaccount():
    if "user_id" not in session or session["role"] != "super_user":
        return redirect(url_for("login"))

    # Get the form data
    username = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")
    phone_number = request.form.get("phone_number")
    privilege = request.form.get("privilege", "view")  # Default to view if not specified

    # Check if email already exists
    existing_email = User.query.filter_by(email=email).first()
    if existing_email:
        flash("Email already exists. Please use a different email.", "error")
        return redirect(url_for("super_user_dashboard"))

    # Check if username already exists
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        flash("Username already exists. Please choose a different username.", "error")
        return redirect(url_for("super_user_dashboard"))

    # Fetch the superuser's details
    superuser = User.query.get(session["user_id"])
    if not superuser:
        flash("Superuser not found.", "error")
        return redirect(url_for("super_user_dashboard"))

    # Create the family member account
    hashed_password = generate_password_hash(password)
    new_user = User(
        username=username,  # Use the provided username
        family_name=superuser.family_name,  # Inherit family name from superuser
        address=superuser.address,  # Inherit address from superuser
        email=email,
        password=hashed_password,
        phone=phone_number,
        role="family_member",
        privilege=privilege,
        status="pending",  # Set initial status as pending
        approved_by=None  # Will be set when approved
    )

    db.session.add(new_user)
    db.session.commit()

    flash("Subaccount created successfully! Waiting for approval.", "success")
    return redirect(url_for("super_user_dashboard"))

@app.route("/update_approval", methods=["POST"])
def update_approval():
    if "user_id" not in session or session["role"] != "super_user":
        return redirect(url_for("login"))

    user_id = request.form.get("user_id")
    action = request.form.get("approve")  # "approve" or "disapprove"

    user = User.query.get(user_id)
    if not user:
        flash("User not found.", "error")
        return redirect(url_for("super_user_dashboard"))

    if action:
        user.status = "approved"
        flash(f"User {user.username} has been approved.", "success")
    else:
        user.status = "pending"
        flash(f"User {user.username} has been disapproved.", "warning")

    db.session.commit()
    return redirect(url_for("super_user_dashboard"))

@app.route('/update_privilege', methods=['POST'])
def update_privilege():
    user_id = request.form.get('user_id')
    new_privilege = request.form.get('new_privilege')
    user = User.query.get(user_id)
   
    if user:
        user.privilege = new_privilege

        db.session.commit()  # Commit both updates together

        flash("Privilege updated successfully!", "success")
    else:
        flash("User not found!", "error")

    return redirect(url_for("super_user_dashboard"))  # Redirect to avoid form resubmission issues

@app.route("/get_categories")
def get_categories():
    categories = Category.query.all()
    return jsonify([{"name": cat.name, "description": cat.category_desc} for cat in categories])

# CODE TO CHECK THE BUDGET STATUS AND SEND ALERTS------------------------->

def check_budget_status(user_id, category_id):
    try:
        with app.app_context():
            # Get budget and expenses in a single query
            budget = Budget.query.filter_by(
                user_id=user_id,
                category_id=category_id,
                month=datetime.now().month,
                year=datetime.now().year
            ).first()

            if not budget:
                return

            # Calculate expenses with a single query
            total_spent = db.session.query(
                db.func.sum(Expense.amount)
            ).filter(
                Expense.user_id == user_id,
                Expense.category_id == category_id,
                Expense.date >= datetime(budget.year, budget.month, 1),
                Expense.date < datetime(budget.year + (budget.month == 12), 
                                     (budget.month % 12) + 1, 1)
            ).scalar() or 0

            if budget.amount > 0:
                percentage = (total_spent / budget.amount) * 100
                if percentage >= 90:  # Only check once for either condition
                    # Get all recipients in one query
                    recipients = [email for (email,) in db.session.query(User.email).filter(
                        db.or_(
                            User.id == user_id,
                            db.and_(
                                User.approved_by == user_id,
                                User.privilege.in_(['view', 'edit'])
                            )
                        )
                    ).all()]
                    
                    if recipients:
                        send_budget_alert_async(
                            recipients,
                            budget.category.name,
                            budget.amount,
                            total_spent,
                            percentage,
                            percentage >= 100
                        )

    except Exception as e:
        print(f"Budget check error: {str(e)}")

def send_budget_alert(recipients, category_name, budget_amount, total_spent, percentage, is_exceeded):
    try:
        current_month = datetime.now().strftime('%B')
        current_year = datetime.now().year
        
        print(f"[DEBUG] Sending {'alert' if is_exceeded else 'warning'} to {recipients}")
        
        if is_exceeded:
            subject = f"🚨 ALERT: Budget Exceeded for {category_name}"
            message = f"""
⚠️ BUDGET ALERT: Your family's spending has exceeded the budget limit!

📊 Category: {category_name}
📅 Month: {current_month} {current_year}
💰 Budget Amount: ₹{float(budget_amount):.2f}
💵 Current Spending: ₹{float(total_spent):.2f}
📈 Percentage Used: {percentage:.1f}%

🚨 Action Required:
- Review your family's expenses
- Consider adjusting spending habits
- Discuss with family members
- Plan for the remaining days

Best regards,
Family Finance Tracker Team
"""
        else:
            subject = f"⚠️ WARNING: Approaching Budget Limit for {category_name}"
            message = f"""
⚠️ BUDGET WARNING: Your family is approaching the budget limit!

📊 Category: {category_name}
📅 Month: {current_month} {current_year}
💰 Budget Amount: ₹{float(budget_amount):.2f}
💵 Current Spending: ₹{float(total_spent)::.2f}
📈 Percentage Used: {percentage:.1f}%

💡 Recommendations:
- Monitor expenses closely
- Review upcoming expenses
- Consider limiting discretionary spending
- Plan remaining budget carefully

Best regards,
Family Finance Tracker Team
"""
        
        with app.app_context():
            msg = Message(
                subject=subject,
                recipients=recipients,
                body=message,
                sender=app.config['MAIL_DEFAULT_SENDER']
            )
            mail.send(msg)
            print(f"[DEBUG] Alert sent successfully to {recipients}")
            
    except Exception as e:
        print(f"[ERROR] Failed to send budget alert: {str(e)}")
        import traceback
        print(traceback.format_exc())

def send_budget_alert_async(recipients, category_name, budget_amount, total_spent, percentage, is_exceeded):
    def send_async():
        with app.app_context():
            try:
                send_budget_alert(recipients, category_name, budget_amount, total_spent, percentage, is_exceeded)
            except Exception as e:
                print(f"Error sending async budget alert: {str(e)}")
    
    Thread(target=send_async).start()

# CODE TO CHECK THE BUDGET STATUS AND SEND ALERTS ENDS HERE NOW------------------------->



# Update add_expense route to check budget after adding expense
@app.route("/add_expense", methods=["POST"])
def add_expense():
    if 'user_id' not in session:
        return jsonify({"message": "Unauthorized"}), 401

    try:
        # Get user context
        user_id = session['user_id']
        role = session['role']
        if role == "family_member":
            user = User.query.get(user_id)
            user_id = user.approved_by
            if not user_id:
                return jsonify({"message": "Not linked to any family"}), 400

        data = request.form.to_dict()
        
        # Quick validation
        if not all([data.get("name"), data.get("category"), data.get("date"), data.get("amount")]):
            return jsonify({"message": "Missing required fields!"}), 400

        # Process form data
        try:
            amount = float(data.get("amount"))
            date = datetime.strptime(data.get("date"), "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return jsonify({"message": "Invalid amount or date format!"}), 400

        # Single database transaction for all operations
        with db.session.begin():
            # Get or create category
            category = Category.query.filter_by(name=data.get("category")).first()
            if not category:
                category = Category(
                    name=data.get("category"),
                    category_desc=data.get("category-desc", "")
                )
                db.session.add(category)
                db.session.flush()

            # Create expense
            new_expense = Expense(
                user_id=user_id,
                name=data.get("name"),
                category_id=category.category_id,
                date=date,
                amount=amount,
                description=data.get("description", "")
            )

            # Handle file if present
            file = request.files.get("file-upload")
            if file and file.filename:
                new_expense.image_data = file.read()
                new_expense.file_type = file.mimetype

            db.session.add(new_expense)
            db.session.flush()

            # Start budget check in background without waiting
            Thread(target=check_budget_status, args=(user_id, category.category_id)).start()

        return jsonify({
            "message": "Expense added successfully!",
            "status": "success"
        })

    except Exception as e:
        db.session.rollback()
        print(f"Error adding expense: {str(e)}")
        return jsonify({
            "message": "Failed to add expense",
            "error": str(e)
        }), 500

@app.route("/get_expenses")
def get_expenses():
    if 'user_id' not in session:
        return jsonify({"message": "Unauthorized"}), 401

    # Consolidated user context logic
    user_id = session['user_id']
    role = session['role']
    
    if role == "family_member":
        user = User.query.get(user_id)
        user_id = user.approved_by
        if not user_id:
            return jsonify({"message": "Not linked to any family"}), 400

    from_date = request.args.get("from_date")
    to_date = request.args.get("to_date")
    page = request.args.get("page", 1, type=int)
    per_page = 10

    query = Expense.query.filter_by(user_id=user_id)
    if from_date:
        query = query.filter(Expense.date >= from_date)
    if to_date:
        query = query.filter(Expense.date <= to_date)

    expenses = query.order_by(Expense.date.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        "expenses": [{
            "id": exp.id,
            "name": exp.name,
            "category": exp.category.name if exp.category else "Unknown",
            "date": exp.date.strftime("%Y-%m-%d"),
            "amount": exp.amount,
            "description": exp.description,
            "image_url": f"/get_file/{exp.id}" if exp.image_data else None,
            "file_type": exp.file_type
        } for exp in expenses.items],
        "total_pages": expenses.pages,
        "current_page": expenses.page
    })

@app.route("/get_expense/<int:expense_id>")
def get_expense(expense_id):
    expense = Expense.query.get(expense_id)
    if not expense:
        return jsonify({"message": "Expense not found"}), 404
    return jsonify({
        "id": expense.id,
        "name": expense.name,
        "category": expense.category.name if expense.category else "Unknown",
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
    if 'user_id' not in session:
        return jsonify({"message": "Unauthorized"}), 401

    # Consolidated user context logic
    user_id = session['user_id']
    role = session['role']
    
    if role == "family_member":
        user = User.query.get(user_id)
        user_id = user.approved_by
        if not user_id:
            return jsonify({"message": "Not linked to any family"}), 400

    # Update query to use the resolved user_id
    expense = Expense.query.filter_by(id=expense_id, user_id=user_id).first()
    if not expense:
        return jsonify({"message": "Expense not found"}), 404

    # Store old category_id to check both old and new categories
    old_category_id = expense.category_id

    data = request.form.to_dict()
    expense.name = data.get("name", expense.name)
    category_name = data.get("category", expense.category.name)
    try:
        expense.amount = float(data.get("amount", expense.amount))
    except ValueError:
        return jsonify({"message": "Invalid amount!"}), 400
    expense.description = data.get("description", expense.description)
    
    category = Category.query.filter_by(name=category_name).first()
    if not category:
        category_desc = data.get("category-desc", "")
        category = Category(name=category_name, category_desc=category_desc)
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

    # Check budget status for both old and new categories-------------------------------->
    check_budget_status(user_id, old_category_id)
    if old_category_id != expense.category_id:
        check_budget_status(user_id, expense.category_id)

    return jsonify({"message": "Expense updated successfully!"})

@app.route("/delete_expense/<int:expense_id>", methods=["DELETE"])
def delete_expense(expense_id):
    if 'user_id' not in session:
        return jsonify({"message": "Unauthorized"}), 401

    # Consolidated user context logic
    user_id = session['user_id']
    role = session['role']
    
    if role == "family_member":
        user = User.query.get(user_id)
        user_id = user.approved_by
        if not user_id:
            return jsonify({"message": "Not linked to any family"}), 400

    expense = Expense.query.filter_by(id=expense_id, user_id=user_id).first()
    if not expense:
        return jsonify({"message": "Expense not found"}), 404

    category_id = expense.category_id
    db.session.delete(expense)
    db.session.commit()
    remaining_expenses = Expense.query.filter_by(category_id=category_id).count()
    if remaining_expenses == 0:
        category = Category.query.get(category_id)
        db.session.delete(category)
        db.session.commit()
    return jsonify({"message": "Expense deleted successfully!"})

@app.route("/get_stats")
def get_stats():
    if 'user_id' not in session:
        return jsonify({"message": "Unauthorized"}), 401

    # Get the correct user context
    user_id = session['user_id']
    role = session['role']
    
    if role == "family_member":
        user = User.query.get(user_id)
        user_id = user.approved_by  # Use super user's ID for family members
        if not user_id:  # Handle unlinked family members
            return jsonify({"message": "Not linked to any family"}), 400
    else:
        user_id = user_id  # Use current user's ID directly for super users

    # Get filter parameters
    from_date = request.args.get("from_date")
    to_date = request.args.get("to_date")

    # Base query
    query = Expense.query.filter_by(user_id=user_id)
    
    # Date filtering
    try:
        if from_date:
            from_date = datetime.strptime(from_date, "%Y-%m-%d").date()
            query = query.filter(Expense.date >= from_date)
        if to_date:
            to_date = datetime.strptime(to_date, "%Y-%m-%d").date()
            query = query.filter(Expense.date <= to_date)
    except ValueError:
        return jsonify({"message": "Invalid date format! Use YYYY-MM-DD"}), 400

    # Rest of the calculations remain the same
    total_spent = query.with_entities(db.func.sum(Expense.amount)).scalar() or 0
    expense_count = query.with_entities(db.func.count(Expense.id)).scalar() or 0
    last_7days_spent = query.with_entities(db.func.sum(Expense.amount)).filter(
        Expense.date >= (datetime.now().date() - timedelta(days=7))
    ).scalar() or 0
    highest_category = query.with_entities(
        Category.name, db.func.sum(Expense.amount)
    ).join(Category).group_by(Category.name).order_by(db.func.sum(Expense.amount).desc()).first()
    highest_amount = query.with_entities(db.func.max(Expense.amount)).scalar() or 0
    # Using decimal Unicode instead of hex
    empty_face = chr(128566)  # Decimal Unicode for 😶
    highest_category_name = highest_category[0] if highest_category else f"Empty!{empty_face}"
    
    return jsonify({
        "total_spent": float(total_spent),
        "expense_count": expense_count,
        "last_7days_spent": float(last_7days_spent),
        "highest_category": highest_category_name,
        "highest_amount": float(highest_amount)
    })

# Modify toggle_recurring route to be simpler
@app.route("/toggle_recurring/<int:budget_id>", methods=["PUT"])
def toggle_recurring(budget_id):

    data = request.get_json()
    recurring = data.get("recurring", False)

    budget = Budget.query.get(budget_id)
    budget.recurring = recurring
    db.session.commit() 
    return jsonify({"message": "Recurring status updated successfully!"})

def check_and_create_recurring_budgets(user_id):
    """Check and create recurring budgets for current month if not already created"""
    try:
        with app.app_context():
            now = datetime.now()
            current_month = now.month
            current_year = now.year
            
            # Get last month's info
            if current_month == 1:
                last_month = 12
                last_year = current_year - 1
            else:
                last_month = current_month - 1
                last_year = current_year
            
            # Find recurring budgets from last month
            recurring_budgets = Budget.query.filter_by(
                user_id=user_id,
                recurring=True,
                month=last_month,
                year=last_year
            ).all()
            
            created_count = 0
            for budget in recurring_budgets:
                # Check if budget already exists for current month
                existing_budget = Budget.query.filter_by(
                    user_id=user_id,
                    category_id=budget.category_id,
                    month=current_month,
                    year=current_year
                ).first()
                
                if not existing_budget:
                    new_budget = Budget(
                        user_id=user_id,
                        category_id=budget.category_id,
                        amount=budget.amount,
                        month=current_month,
                        year=current_year,
                        recurring=True
                    )
                    db.session.add(new_budget)
                    created_count += 1
            
            if created_count > 0:
                db.session.commit()
                print(f"[DEBUG] Created {created_count} recurring budgets for {current_month}/{current_year}")
                
    except Exception as e:
        print(f"[ERROR] Failed to create recurring budgets: {str(e)}")
        db.session.rollback()

@app.route("/add_budget", methods=["POST"])
def add_budget():
    if 'user_id' not in session:
        return jsonify({"message": "Unauthorized"}), 401

    # Consolidated user context logic
    user_id = session['user_id']
    role = session['role']
    
    if role == "family_member":
        user = User.query.get(user_id)
        user_id = user.approved_by
        if not user_id:
            return jsonify({"message": "Not linked to any family"}), 400

    user_id = session['user_id']
    data = request.form.to_dict()
    year = data.get("year")
    month = data.get("month")
    category_name = data.get("budget-category")  # Remove conversion
    amount = data.get("budget-amount")

    if not year or not month or not category_name or not amount:
        return jsonify({"message": "Missing required fields!"}), 400

    try:
        amount = float(amount)
    except ValueError:
        return jsonify({"message": "Invalid amount!"}), 400

    category = Category.query.filter_by(name=category_name).first()
    if not category:
        category = Category(name=category_name)
        db.session.add(category)
        db.session.commit()

    # Check if budget already exists for the given year, month, and category
    existing_budget = Budget.query.filter_by(user_id=user_id, year=year, month=month, category_id=category.category_id).first()
    if existing_budget:
        return jsonify({"message": "Budget already set for this year, month, and category!"}), 400

    new_budget = Budget(
        user_id=user_id,
        category_id=category.category_id,
        amount=amount,
        month=int(month),
        year=int(year)
    )
    db.session.add(new_budget)
    db.session.commit()

    return jsonify({"message": "Budget added successfully!"})

@app.route("/get_budgets")
def get_budgets():
    if 'user_id' not in session:
        return jsonify({"message": "Unauthorized"}), 401

    user_id = session['user_id']
    role = session['role']
    
    if role == "family_member":
        user = User.query.get(user_id)
        if user.privilege not in ['view', 'edit']:
            return jsonify({"message": "Insufficient privileges"}), 403
        user_id = user.approved_by
        if not user_id:
            return jsonify({"message": "Not linked to any family"}), 400

    page = request.args.get("page", 1, type=int)
    per_page = 10

    budgets = Budget.query.filter_by(user_id=user_id).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({
        "budgets": [{
            "id": budget.budget_id,
            "year": budget.year,
            "month": budget.month,
            "category": budget.category.name if budget.category else "Unknown",
            "amount": budget.amount,
            "recurring": budget.recurring
        } for budget in budgets.items],
        "total_pages": budgets.pages,
        "current_page": budgets.page
    })

@app.route("/get_budget/<int:budget_id>")
def get_budget(budget_id):
    budget = Budget.query.get(budget_id)
    if not budget:
        return jsonify({"message": "Budget not found"}), 404
        
    # Add privilege check for family members
    if session.get('role') == "family_member":
        user = User.query.get(session['user_id'])
        if user.privilege not in ['view', 'edit']:
            return jsonify({"message": "Insufficient privileges"}), 403

    return jsonify({
        "id": budget.budget_id,
        "year": budget.year,
        "month": budget.month,
        "category": budget.category.name if budget.category else "Unknown",
        "amount": budget.amount,
        "recurring": budget.recurring
    })

# Edit Budget --------->
@app.route("/edit_budget/<int:budget_id>", methods=["PUT"])
def edit_budget(budget_id):
    if 'user_id' not in session:
        return jsonify({"message": "Unauthorized"}), 401

    user_id = session['user_id']
    budget = Budget.query.filter_by(budget_id=budget_id, user_id=user_id).first()
    if not budget:
        return jsonify({"message": "Budget not found"}), 404

    data = request.form.to_dict()
    print("Editing Budget ID:", budget_id)  # DEBUGGING REMOVE IT DURING DEPLOYMENT
    print("Received Data:", data)  # DEBUGGING REMOVE IT DURING DEPLOYMENT

    year = data.get("year", budget.year)
    month = data.get("month", budget.month)
    category_name = data.get("budget-category", budget.category.name)  # Remove conversion
    try:
        amount = float(data.get("budget-amount", budget.amount))
    except ValueError:
        return jsonify({"message": "Invalid amount!"}), 400

    category = Category.query.filter_by(name=category_name).first()
    if not category:
        category = Category(name=category_name)
        db.session.add(category)
        db.session.commit()

    # Check if budget already exists for the given year, month, and category
    existing_budget = Budget.query.filter_by(user_id=user_id, year=year, month=month, category_id=category.category_id).first()
    if existing_budget and existing_budget.budget_id != budget_id:
        return jsonify({"message": "Budget already set for this year, month, and category!"}), 400

    budget.year = year
    budget.month = month
    budget.amount = amount
    budget.category_id = category.category_id
    db.session.commit()
    return jsonify({"message": "Budget updated successfully!"})


# Delete budget--------->
@app.route("/delete_budget/<int:budget_id>", methods=["DELETE"])
def delete_budget(budget_id):
    if 'user_id' not in session:
        return jsonify({"message": "Unauthorized"}), 401

    user_id = session['user_id']
    budget = Budget.query.filter_by(budget_id=budget_id, user_id=user_id).first()
    if not budget:
        return jsonify({"message": "Budget not found"}), 404

    db.session.delete(budget)
    db.session.commit()
    return jsonify({"message": "Budget deleted successfully!"})

@app.route('/logout')
def logout():
    session.clear() # Clear all session data
    return redirect(url_for('login'))



# TEAM 4 (Graph)-------------------------- STARTS HERE(and add code related to it below this line) ---->

@app.route('/plot/category_data/<int:year>/<int:month>')
def get_category_plot(year, month):
    user_id = session.get('user_id')
    category_plot = generate_category_expenses_plot(month=month, year=year,user_id=user_id)
    return jsonify({'category_plot': category_plot})

@app.route('/plot/pie_chart/<int:year>/<int:month>')
def get_pie_chart(year, month):
    user_id = session.get('user_id')
    pie_chart = generate_pie_chart(user_id=user_id, month=month, year=year)
    return jsonify({'pie_chart': pie_chart})

@app.route('/plot/bar_chart/<int:year>/<int:month>')
def get_bar_chart(year, month):
    user_id = session.get('user_id')
    bar_chart = generate_bar_chart(user_id=user_id, month=month, year=year)
    return jsonify({'bar_chart': bar_chart})

@app.route('/plot/stacked_bar_chart/<int:year>/<int:month>')
def get_stacked_bar_chart(year, month):
    user_id = session.get('user_id')
    stacked_bar_chart = generate_stacked_bar_chart(user_id=user_id, month=month, year=year)
    return jsonify({'stacked_bar_chart': stacked_bar_chart})

@app.route('/plot/line_chart/<int:year>')
def get_line_chart(year):
    user_id = session.get('user_id')
    line_chart = generate_line_chart(user_id=user_id,year=year)
    return jsonify({'line_chart': line_chart})




# FOR SAVINGS BUTTON WORKING (TEAM 3+4)-------------------------- STARTS HERE(and add code related to it below this line) ---->
@app.route('/savings_dashboard')
@login_required
def savings_dashboard():
    if not session.get('verified'):
        return redirect(url_for('verify'))
    
    return "<h1>Savings Dashboard - Coming Soon!</h1>"  # Placeholder for now


with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)
