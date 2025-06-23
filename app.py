from flask import Flask, request, render_template, redirect, session, url_for, flash
from database import db
from database import User
import joblib
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///budgetbuddy.db'
db.init_app(app)

# ----------------------------- User Authentication  -----------------------------

def hash_password(password):
    return password 

def verify_password(password, hashed):
    return password == hashed  

# ----------------------------- Load ML Models -----------------------------

base_dir = os.path.dirname(os.path.abspath(__file__))
model = joblib.load(os.path.join(base_dir, "models", "model.pkl"))
vectorizer = joblib.load(os.path.join(base_dir, "models", "vectorizer.pkl"))

budget_predictor = joblib.load(os.path.join(base_dir, "models", "budget_predictor.pkl"))
budget_scaler = joblib.load(os.path.join(base_dir, "models", "budget_scaler.pkl"))

# ----------------------------- Predict Functions -----------------------------

def predict_category(description):
    X = vectorizer.transform([description])
    prediction = model.predict(X)
    return prediction[0]

def predict_budget_allocation(income, rent):
    disposable_income = income - rent
    if disposable_income <= 0:
        raise ValueError("Disposable income must be greater than zero.")
    input_data = [[disposable_income]]
    input_scaled = budget_scaler.transform(input_data)
    predicted_values = budget_predictor.predict(input_scaled)[0]
    categories = [
        "Monthly_shopping", "Grooming", "Mess", "Transport", "Eating_Out(JUNK)",
        "Entertainment", "Utilities", "Healthcare", "Saving", "Miscellaneous"
    ]
    return dict(zip(categories, predicted_values))

# -----------------------------  Categories -----------------------------

categories = {
    "Rent": {"total": 0, "items": []},
    "Monthly_shopping": {"total": 0, "items": []},
    "Grooming": {"total": 0, "items": []},
    "Mess": {"total": 0, "items": []},
    "Transport": {"total": 0, "items": []},
    "Eating_Out(JUNK)": {"total": 0, "items": []},
    "Entertainment": {"total": 0, "items": []},
    "Utilities": {"total": 0, "items": []},
    "Healthcare": {"total": 0, "items": []},
    "Saving": {"total": 0, "items": []},
    "Miscellaneous": {"total": 0, "items": []}
}

# ----------------------------- Auth Routes -----------------------------

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not username or not email or not password or not confirm_password:
            flash('Please fill all fields', 'error')
            return render_template('signup.html', username=username, email=email)

        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('signup.html', username=username, email=email)

        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('signup.html', username=username, email=email)

        hashed = hash_password(password)
        new_user = User(username=username, email=email, password=hashed)

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Signup successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f"Database error: {e}", 'error')
            return render_template('signup.html', username=username, email=email)

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and verify_password(password, user.password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'error')

    return render_template('login.html')

# ----------------------------- Main Pages -----------------------------

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])

    total_balance = 5000
    total_expenses = 1500
    total_income = 3000
    goal = 10000
    budget_usage_percent = (total_expenses / goal) * 100 if goal else 0

    recent_transactions = [
        {'date': '2025-05-21', 'description': 'Groceries', 'amount': 800},
        {'date': '2025-05-20', 'description': 'Recharge', 'amount': 300},
    ]

    return render_template(
        'dashboard.html',
        username=user.username,
        total_balance=total_balance,
        total_expenses=total_expenses,
        total_income=total_income,
        goal=goal,
        recent_transactions=recent_transactions,
        budget_usage_percent=round(budget_usage_percent, 2)
    )

@app.route('/expenses')
def expense_tracker():
    username = "User"  
    return render_template('expense_tracker.html', categories=categories, username=username)

@app.route('/add_expense', methods=['POST'])
def add_expense():
    amount = request.form.get('amount')
    description = request.form.get('description', '')
    return_page = request.form.get('return_page', 'expense_tracker')

    try:
        amount = float(amount)
    except (ValueError, TypeError):
        flash("Invalid amount entered.", "error")
        return redirect(url_for(return_page))

    if not description:
        flash("Description is required.", "error")
        return redirect(url_for(return_page))

    predicted_category = predict_category(description)

    if predicted_category not in categories:
        categories[predicted_category] = {"total": 0, "items": []}

    categories[predicted_category]["total"] += amount
    categories[predicted_category]["items"].append({
        "amount": amount,
        "description": description
    })

    flash(f"Added expense to category: {predicted_category}", "success")
    return redirect(url_for(return_page))

@app.route('/wallet')
def wallet():
    return render_template('wallet.html')

@app.route('/profile')
def profile():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    user = User.query.get(user_id)
    if not user:
        return redirect(url_for('login'))

    return render_template('profile.html', name=user.username, email=user.email)

# ----------------------------- AI Budget Planner -----------------------------

@app.route('/ai-planner', methods=['GET', 'POST'])
def ai_budget():
    result = None
    income = None
    rent = None

    if request.method == 'POST':
        try:
            income = float(request.form['income'])
            rent = float(request.form['rent'])
            result = predict_budget_allocation(income, rent)
        except ValueError as ve:
            flash(str(ve), 'error')
        except Exception as e:
            flash("Error predicting budget: " + str(e), 'error')

    return render_template('ai_budget.html', predictions=result, income=income, rent=rent)


# ----------------------------- Main -----------------------------

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
