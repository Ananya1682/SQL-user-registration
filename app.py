from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from mysql.connector import Error
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Needed for flash messages and CSRF protection

# MySQL configuration
db_config = {
    'host': 'localhost',
    'user': 'root',        # Replace with your MySQL username
    'password': 'ananya1682',        # Replace with your MySQL password
    'database': 'user_db'
}

# Define the registration form using Flask-WTF
class RegistrationForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=2, max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=100)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Register')

# Define the edit form
class EditForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=2, max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=2, max=50)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=100)])
    password = PasswordField('Password', validators=[Length(min=6)])
    submit = SubmitField('Update')

def get_db_connection():
    """Establishes a connection to the MySQL database."""
    try:
        connection = mysql.connector.connect(**db_config)
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

@app.route('/')
def index():
    return redirect(url_for('register'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        # Get form data
        first_name = form.first_name.data
        last_name = form.last_name.data
        email = form.email.data
        password = form.password.data

        # Hash the password
        hashed_password = generate_password_hash(password)

        # Insert into database
        connection = get_db_connection()
        if connection:
            cursor = connection.cursor()
            try:
                cursor.execute("""
                    INSERT INTO users (first_name, last_name, email, password)
                    VALUES (%s, %s, %s, %s)
                """, (first_name, last_name, email, hashed_password))
                connection.commit()
                flash('Registration successful!', 'success')
                return redirect(url_for('view_users'))
            except mysql.connector.Error as err:
                if err.errno == 1062:  # Duplicate entry
                    flash('Error: Email already exists.', 'danger')
                else:
                    flash(f"Error: {err}", 'danger')
            finally:
                cursor.close()
                connection.close()
    return render_template('register.html', form=form)

@app.route('/view')
def view_users():
    connection = get_db_connection()
    users = []
    if connection:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT id, first_name, last_name, email, registration_date FROM users ORDER BY registration_date DESC")
        users = cursor.fetchall()
        cursor.close()
        connection.close()
    return render_template('view.html', users=users)

@app.route('/edit/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    form = EditForm()
    connection = get_db_connection()
    if not connection:
        flash('Database connection failed.', 'danger')
        return redirect(url_for('view_users'))
    cursor = connection.cursor(dictionary=True)
    if request.method == 'GET':
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if user:
            form.first_name.data = user['first_name']
            form.last_name.data = user['last_name']
            form.email.data = user['email']
        else:
            flash('User not found.', 'danger')
            cursor.close()
            connection.close()
            return redirect(url_for('view_users'))
    if form.validate_on_submit():
        first_name = form.first_name.data
        last_name = form.last_name.data
        email = form.email.data
        password = form.password.data

        if password:
            hashed_password = generate_password_hash(password)
            sql = "UPDATE users SET first_name=%s, last_name=%s, email=%s, password=%s WHERE id=%s"
            params = (first_name, last_name, email, hashed_password, user_id)
        else:
            sql = "UPDATE users SET first_name=%s, last_name=%s, email=%s WHERE id=%s"
            params = (first_name, last_name, email, user_id)
        try:
            cursor.execute(sql, params)
            connection.commit()
            flash('User updated successfully!', 'success')
            return redirect(url_for('view_users'))
        except mysql.connector.Error as err:
            if err.errno == 1062:  # Duplicate entry
                flash('Error: Email already exists.', 'danger')
            else:
                flash(f"Error: {err}", 'danger')
    cursor.close()
    connection.close()
    return render_template('edit.html', form=form, user_id=user_id)

@app.route('/delete/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            connection.commit()
            flash('User deleted successfully!', 'success')
        except mysql.connector.Error as err:
            flash(f"Error: {err}", 'danger')
        finally:
            cursor.close()
            connection.close()
    else:
        flash('Database connection failed.', 'danger')
    return redirect(url_for('view_users'))

if __name__ == '__main__':
    app.run(debug=True)
