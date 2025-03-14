import matplotlib
matplotlib.use('Agg')  # Use a non-interactive backend
import matplotlib.pyplot as plt
import pandas as pd
import io
import base64
from datetime import datetime
from models import db, Expense, Category, Budget, User

def generate_monthly_expenses_plot():
    # Query to get monthly expenses
    monthly_expenses = db.session.query(
        db.func.strftime('%Y-%m', Expense.date).label('month'),
        db.func.sum(Expense.amount).label('total_expense')
    ).group_by('month').order_by('month').all()

    # Check if data is retrieved
    print("Monthly Expenses Data:", monthly_expenses)  # Debugging line

    # Extract data for plotting
    months = [row.month for row in monthly_expenses]
    expenses = [float(row.total_expense) for row in monthly_expenses]

    # Generate the plot
    plt.figure(figsize=(8, 5))
    plt.plot(months, expenses, marker='o', linestyle='-', color='b')
    plt.xlabel('Month')
    plt.ylabel('Total Expense')
    plt.title('Monthly Expenses')
    plt.xticks(rotation=45)
    plt.grid()

    # Save the plot to a BytesIO object
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()

    # Return the plot as a base64-encoded string
    encoded_string = base64.b64encode(img.getvalue()).decode()
    print("Encoded Monthly Expenses Plot:", encoded_string)  # Debugging line
    return encoded_string

def generate_category_expenses_plot(year, month):
    # Query to get expenses by category for a specific month and year
    category_expenses = db.session.query(
        Category.name,
        db.func.sum(Expense.amount).label('total_expense')
    ).join(Expense, Category.category_id == Expense.category_id).filter(db.func.strftime('%Y', Expense.date) == str(year)).filter(db.func.strftime('%m', Expense.date) == f'{month:02d}').group_by(Category.name).all()

    # Extract data for plotting
    categories = [row.name for row in category_expenses]
    expenses = [float(row.total_expense) for row in category_expenses]

    # Generate the plot
    plt.figure(figsize=(8, 5))
    plt.bar(categories, expenses, color='orange')
    plt.xlabel('Category')
    plt.ylabel('Total Expense')
    plt.title(f'Expenses by Category for {year}-{month:02d}')
    plt.xticks(rotation=45)

    # Save the plot to a BytesIO object
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()

    # Return the plot as a base64-encoded string
    return base64.b64encode(img.getvalue()).decode()


def generate_pie_chart(user=None, month=None, year=None):
    if month is None or year is None:
        today = datetime.today()
        month, year = today.month, today.year

    # Query for budget data
    budget_data = db.session.query(
        Category.name,
        db.func.sum(Budget.amount).label('total_budget')
    ).join(Budget, Category.category_id == Budget.category_id).filter(Budget.month == month).filter(Budget.year == year).group_by(Category.name).all()

    # Query for expense data
    expense_data = db.session.query(
        Category.name,
        db.func.sum(Expense.amount).label('total_expense')
    ).join(Expense, Category.category_id == Expense.category_id).filter(db.func.strftime('%m', Expense.date) == f'{month:02d}').filter(db.func.strftime('%Y', Expense.date) == str(year)).group_by(Category.name).all()

    # Extract data for plotting
    categories_budget = [row.name for row in budget_data]
    budget_amounts = [float(row.total_budget) for row in budget_data]

    categories_expense = [row.name for row in expense_data]
    expense_amounts = [float(row.total_expense) for row in expense_data]

    # Generate the plot
    fig, axs = plt.subplots(1, 2, figsize=(12, 6))

    if budget_amounts:
        axs[0].pie(budget_amounts, labels=categories_budget, autopct='%1.1f%%', startangle=140)
        axs[0].set_title('Planned Budget')
    else:
        axs[0].text(0.5, 0.5, "No Data", fontsize=15, ha='center')

    if expense_amounts:
        axs[1].pie(expense_amounts, labels=categories_expense, autopct='%1.1f%%', startangle=140)
        axs[1].set_title('Actual Expenses')
    else:
        axs[1].text(0.5, 0.5, "No Data", fontsize=15, ha='center')

    # Save the plot to a BytesIO object
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()

    return base64.b64encode(img.getvalue()).decode()


def generate_bar_chart(user=None, month=None, year=None):
    if month is None or year is None:
        today = datetime.today()
        month, year = today.month, today.year

    # Query to get budget and expense data for the user
    data = db.session.query(
        Category.name,
        db.func.sum(Budget.amount).label('total_budget'),
        db.func.sum(Expense.amount).label('total_expense')
    ).join(Budget, Category.category_id == Budget.category_id, isouter=True).join(Expense, Category.category_id == Expense.category_id, isouter=True).filter(Budget.user_id == User.id).filter(db.func.strftime('%m', Expense.date) == f'{month:02d}').filter(db.func.strftime('%Y', Expense.date) == str(year)).group_by(Category.name).all()

    total_budget = sum(row[1] for row in data)
    total_expense = sum(row[2] for row in data)
    fig, ax = plt.subplots(figsize=(12, 6))  #  Make it WIDER
    if not data or all(row[1] == 0 and row[2] == 0 for row in data):
        ax.text(0.5, 0.5, "No Data Available", fontsize=15, ha='center', va='center')
    else:
        categories = [row[0] for row in data]
        budgets = [row[1] for row in data]
        expenses = [row[2] for row in data]
        x_indexes = range(len(categories))
        ax.barh(x_indexes, budgets, height=0.8, color='aqua', label="Budget", alpha=0.6)
        ax.barh(x_indexes, expenses, height=0.8, color='red', label="Expense", alpha=0.6)
        ax.set_yticks(x_indexes)
        ax.set_yticklabels(categories)
        ax.set_xlabel("Amount")
        ax.set_title(f"Spending Progress by Category ({month}/{year})")
        ax.legend()
        legend_text = f"Total Budget: Rs.{total_budget:,.2f}\nTotal Spent: Rs.{total_expense:,.2f}"  #  Keep Total Budget and Total Spent Label
        ax.text(1.05, 0.98, legend_text, transform=ax.transAxes, fontsize=12, verticalalignment='top', 
                bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.5'))
    img = io.BytesIO()
    plt.savefig(img, format="png", bbox_inches="tight")
    img.seek(0)
    plt.close()

    # Return the plot as a base64-encoded string
    return base64.b64encode(img.getvalue()).decode()

def generate_stacked_bar_chart(month=None, year=None):
    if month is None or year is None:
        today = datetime.today()
        month, year = today.month, today.year

    # Query to get expenses by family members and categories
    data = db.session.query(
        User.username,
        Category.name,
        db.func.sum(Expense.amount).label('total_expense')
    ).join(Expense, User.id == Expense.user_id).join(Category, Expense.category_id == Category.category_id).filter(
        db.func.strftime('%m', Expense.date) == f'{month:02d}'
    ).filter(
        db.func.strftime('%Y', Expense.date) == str(year)
    ).group_by(User.username, Category.name).all()

    # Convert to a DataFrame
    df = pd.DataFrame(data, columns=['username', 'category', 'total_expense'])

    if df.empty:
        print("❗ No expense data found for this month and year. Returning empty plot.")
        return None  # Return None to indicate no data

    df_pivot = df.pivot(index='username', columns='category', values='total_expense').fillna(0)

    df_pivot = df_pivot.apply(pd.to_numeric, errors='coerce').fillna(0)



    # Generate the plot
    plt.figure(figsize=(12, 6))
    df_pivot.plot(kind='bar', stacked=True, colormap='Set2', edgecolor='black')
    plt.xlabel('Family Members')
    plt.ylabel('Total Expense')
    plt.title(f'Family Members\' Expenses by Category for {month}/{year}')
    plt.xticks(rotation=0)
    plt.legend(title='Category', bbox_to_anchor=(1.05, 1), loc='upper left')

    # Save the plot to a BytesIO object
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    img.seek(0)
    plt.close()

    # Return the plot as a base64-encoded string
    return base64.b64encode(img.getvalue()).decode()


def generate_line_chart(year):
    # Query to get budget and expense data for the year
    data = db.session.query(
        db.func.strftime('%m', Expense.date).label('month'),
        db.func.sum(Budget.amount).label('total_budget'),
        db.func.sum(Expense.amount).label('total_expense')
    ).join(Budget, (Budget.category_id == Expense.category_id) & 
                   (Budget.month == db.func.strftime('%m', Expense.date)), isouter=True
    ).filter(db.func.strftime('%Y', Expense.date) == str(year)
    ).group_by('month').order_by('month').all()

    # Convert data into lists
    months = [row.month for row in data]
    total_budget = [float(row.total_budget) if row.total_budget else 0 for row in data]
    total_expense = [float(row.total_expense) if row.total_expense else 0 for row in data]
    
    plt.figure(figsize=(10, 5))
    plt.plot(months, total_budget, label='Budget', marker='o', linestyle='-')
    plt.plot(months, total_expense, label='Expense', marker='o', linestyle='-')
    plt.xlabel('Month')
    plt.ylabel('Amount')
    plt.title(f'Budget vs. Expense by Month ({year})')
    plt.legend()
    plt.grid()
    # Save the plot to a BytesIO object
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()

    # Return the plot as a base64-encoded string
    return base64.b64encode(img.getvalue()).decode()