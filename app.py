
import os

from flask import (
    Flask, render_template, request,
    redirect, url_for, flash
)

from flask_login import (
    LoginManager, UserMixin,
    login_user, login_required,
    logout_user, current_user
)

from flask_wtf.csrf import CSRFProtect
from werkzeug.security import check_password_hash

from dotenv import load_dotenv
from db import get_db_connection


# Load environment variables
load_dotenv()

# Initialize Flask
app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

if not app.config["SECRET_KEY"]:
    raise RuntimeError("SECRET_KEY is missing from .env")

app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = False  # Enable HTTPS in production


# Enable CSRF protection
csrf = CSRFProtect(app)


# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "Please log in to access this page."


# Admin configuration
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH")

if not ADMIN_USERNAME or not ADMIN_PASSWORD_HASH:
    raise RuntimeError("Admin credentials are missing from .env")


# Admin user
class Admin(UserMixin):

    def __init__(self, user_id):
        self.id = user_id


@login_manager.user_loader
def load_user(user_id):

    if user_id == "1":
        return Admin("1")

    return None


# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():

    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':

        username = request.form.get('username', '')
        password = request.form.get('password', '')

        if (
            username == ADMIN_USERNAME
            and check_password_hash(ADMIN_PASSWORD_HASH, password)
        ):
            login_user(Admin("1"))
            return redirect(url_for('index'))

        flash("Invalid username or password.", "error")

    return render_template('login.html')


# Logout route
@app.route('/logout', methods=['POST'])
@login_required
def logout():

    logout_user()
    flash("You have been logged out.", "success")

    return redirect(url_for('login'))


# Display employees
@app.route('/')
@login_required
def index():

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute("SELECT * FROM employees ORDER BY id")
        employees = cursor.fetchall()

        return render_template('index.html', employees=employees)

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


# Add employee
@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_employee():

    if request.method == 'POST':

        connection = None
        cursor = None

        try:
            name = request.form['name'].strip()
            email = request.form['email'].strip()
            phone = request.form['phone'].strip()
            department = request.form['department'].strip()
            designation = request.form['designation'].strip()
            salary = request.form['salary']

            if not all([
                name, email, phone,
                department, designation, salary
            ]):
                flash("All fields are required.", "error")
                return redirect(url_for('add_employee'))

            connection = get_db_connection()
            cursor = connection.cursor()

            query = """
                INSERT INTO employees
                (name, email, phone, department, designation, salary)
                VALUES (%s, %s, %s, %s, %s, %s)
            """

            values = (
                name, email, phone,
                department, designation, salary
            )

            cursor.execute(query, values)
            connection.commit()

            flash("Employee added successfully.", "success")

        finally:
            if cursor:
                cursor.close()

            if connection and connection.is_connected():
                connection.close()

        return redirect(url_for('index'))

    return render_template('add_employee.html')


# Edit employee
@app.route('/edit/<int:employee_id>', methods=['GET', 'POST'])
@login_required
def edit_employee(employee_id):

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        if request.method == 'POST':

            name = request.form['name'].strip()
            email = request.form['email'].strip()
            phone = request.form['phone'].strip()
            department = request.form['department'].strip()
            designation = request.form['designation'].strip()
            salary = request.form['salary']

            if not all([
                name, email, phone,
                department, designation, salary
            ]):
                flash("All fields are required.", "error")
                return redirect(url_for(
                    'edit_employee',
                    employee_id=employee_id
                ))

            query = """
                UPDATE employees
                SET name = %s,
                    email = %s,
                    phone = %s,
                    department = %s,
                    designation = %s,
                    salary = %s
                WHERE id = %s
            """

            values = (
                name, email, phone,
                department, designation, salary,
                employee_id
            )

            cursor.execute(query, values)
            connection.commit()

            flash("Employee updated successfully.", "success")
            return redirect(url_for('index'))

        cursor.execute(
            "SELECT * FROM employees WHERE id = %s",
            (employee_id,)
        )

        employee = cursor.fetchone()

        if employee is None:
            return "Employee not found", 404

        return render_template(
            'edit_employee.html',
            employee=employee
        )

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()


# Delete employee
@app.route('/delete/<int:employee_id>', methods=['POST'])
@login_required
def delete_employee(employee_id):

    connection = None
    cursor = None

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            "DELETE FROM employees WHERE id = %s",
            (employee_id,)
        )

        connection.commit()

        if cursor.rowcount:
            flash("Employee deleted successfully.", "success")
        else:
            flash("Employee not found.", "error")

    finally:
        if cursor:
            cursor.close()

        if connection and connection.is_connected():
            connection.close()

    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
