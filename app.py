from flask import Flask, render_template, request, redirect, session, jsonify, url_for
from db_connection import Db  # Import the Db class
import os
import hashlib  # For password hashing
import bcrypt
import re
from mysql.connector import IntegrityError
import traceback

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')



@app.route('/')
def main():
    return render_template("login/login.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        try:
            if not email or not password:
                return jsonify({"success": False, "error": "Email and password required"}), 400

            # Determine role and redirect URL
            role = 'Customer'
            redirect_url = url_for('home')
            if '@admin' in email:
                role = 'Admin'
                redirect_url = url_for('admin')
            elif '@staff' in email:
                role = 'Staff'
                redirect_url = url_for('staff')
            elif '@manager' in email:
                role = 'Manager'
                redirect_url = url_for('manager')

            db = Db()
            
            try:
                # Check Users table
                user = db.selectOne(
                    "SELECT user_id, password, role FROM Users WHERE email = %s",
                    (email,)
                )
                
                # Create new system user if not exists
                if not user and role != 'Customer':
                    username = email.split('@')[0]
                    if not re.match(r'^[a-zA-Z0-9_]+$', username):
                        return jsonify({"success": False, "error": "Invalid username format"}), 400

                    try:
                        # First check Admin table credentials
                        admin_user = db.selectOne(
                            "SELECT email, password FROM Admin WHERE email = %s AND password = %s",
                            (email, password)
                        )
                        if not admin_user:
                            return jsonify({"success": False, "error": "Invalid admin credentials"}), 401
                            
                        # Create user only if admin credentials are valid
                        user_id = db.insert(
                            "INSERT INTO Users (username, email, password, role) VALUES (%s, %s, %s, %s)",
                            (username, email, password, role)
                        )
                        db.commit()
                        user = db.selectOne(
                            "SELECT user_id, password, role FROM Users WHERE email = %s",
                            (email,)
                        )

                    except Exception as e:
                        db.rollback()
                        raise

                # Validate credentials for all users
                if user and user['password'] == password:
                    session.update({
                        'user_id': user['user_id'],
                        'role': user['role']
                    })
                    
                    # For customers, ensure Customer record exists
                    if user['role'] == 'Customer':
                        customer = db.selectOne(
                            "SELECT customer_id FROM Customer WHERE user_id = %s",
                            (user['user_id'],)
                        )
                        if not customer:
                            db.insert("INSERT INTO Customer (user_id) VALUES (%s)", (user['user_id'],))
                            db.commit()
                    
                    return jsonify({
                        "success": True,
                        "redirect": redirect_url
                    })
                
                return jsonify({"success": False, "error": "Invalid credentials"}), 401

            except IntegrityError as e:
                db.rollback()
                return jsonify({"success": False, "error": "User already exists"}), 409
            except Exception as db_error:
                db.rollback()
                print(f"Database error: {str(db_error)}")
                return jsonify({"success": False, "error": "Database operation failed"}), 500

        except Exception as e:
            print(f"General error: {traceback.format_exc()}")
            return jsonify({"success": False, "error": "Internal server error"}), 500

    return render_template('login/login.html')

@app.route('/home')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template("/home/index.html")

def validate_email(email):
    # More comprehensive email regex
    return re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = request.get_json()
        db = Db()
        try:
            # Validate fields
            email = data['email'].lower().strip()
            phone_number = str(data['phone_number'])
            password = data['password']
            customer_name = data['customer_name'].strip()

            # Validate email format
            if not validate_email(email):
                return jsonify({'error': 'Invalid email format'}), 400

            # Validate phone number
            if not re.match(r'^\d{10}$', phone_number):
                return jsonify({'error': 'Invalid phone number'}), 400

            # Check if email exists in Users table
            if db.selectOne("SELECT email FROM Users WHERE email = %s", (email,)):
                return jsonify({'error': 'Email already registered'}), 409

            # Insert into Users table
            user_id = db.insert(
                """INSERT INTO Users 
                (username, email, password, role) 
                VALUES (%s, %s, %s, 'Customer')""",
                (customer_name, email, password)
            )
            
            # Insert into Customer table (only user_id as per schema)
            db.insert(
                "INSERT INTO Customer (user_id) VALUES (%s)",
                (user_id,)
            )
            
            db.commit()
            return jsonify({'success': True, 'redirect': url_for('login')}), 201

        except IntegrityError as e:
            return jsonify({'error': 'Registration conflict'}), 409
        except Exception as e:
            print(f"Signup error: {str(e)}")
            return jsonify({'error': 'Registration failed'}), 500

    return render_template('login/signup.html')




def render_admin_template(template):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template(f"admin/pages/{template}")
    return render_template('admin/index.html')

@app.route('/admin')
def admin_home():
    return render_template('admin/index.html')

@app.route('/admin/users')
def admin_users():
    return render_template('admin/pages/users.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    return render_template('admin/pages/dashboard.html')

@app.route('/admin/notifications')
def admin_notification():
    return render_template('admin/pages/notifications.html')

@app.route('/admin/sales')
def admin_sales():
    return render_template('admin/pages/sales.html')

@app.route('/admin/security')
def admin_security():
    return render_template('admin/pages/security.html')



@app.route('/manager')
def manager():

    return render_template("manager/index.html")


@app.route('/staff')
def staff():

    return render_template("staff/index.html")






if __name__ == '__main__':
    app.run(debug=True)
