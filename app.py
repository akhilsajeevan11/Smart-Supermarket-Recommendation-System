from flask import Flask, render_template, request, redirect, session, jsonify, url_for
from db_connection import Db  # Import the Db class
import os
import hashlib  # For password hashing
import bcrypt
import re
from mysql.connector import IntegrityError

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')



@app.route('/')
def main():
    return render_template("login/login.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        data = request.get_json()
        username = data.get('textfield', '').strip()
        password = data.get('textfield2', '')
        
        try:
            if not username or not password:
                return jsonify({"success": False, "error": "Username/Email and password required"}), 400

            # Check if input is email (customer login)
            if '@' in username:
                db = Db()
                customer = db.selectOne(
                    "SELECT customer_id, email, password FROM customer WHERE email = %s", 
                    (username,)
                )
                
                if customer:
                    hashed_input = hashlib.sha256(password.encode()).hexdigest()
                    if hashed_input == customer.get('password'):
                        session['user_id'] = customer.get('customer_id')
                        session['user_type'] = 'customer'
                        return jsonify({
                            "success": True,
                            "redirect": url_for('home')
                        })

            # Staff login
            db = Db()
            user = db.selectOne(
                "SELECT login_id, password, user_type FROM login WHERE username = %s", 
                (username,)
            )
            
            if user and bcrypt.checkpw(password.encode(), user.get('password', '').encode()):
                session['user_id'] = user.get('login_id')
                session['user_type'] = user['user_type']
                return jsonify({
                    "success": True,
                    "redirect": url_for('admin_dashboard' if user['user_type'] == 'manager' else 'staff_dashboard')
                })

            return jsonify({
                "success": False,
                "error": "Invalid credentials"
            }), 401

        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"Login error: {str(e)}"
            }), 500
        
    return render_template("login/login.html")

@app.route('/home')
def home():
    # if 'user_id' not in session:
    #     return redirect('/')
    return render_template("index.html")

def validate_email(email):
    # More comprehensive email regex
    return re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = request.get_json()
        
        # Validate required fields first
        required_fields = ['customer_name', 'email', 'phone_number', 'password']
        if not all(field in data for field in required_fields):
            return jsonify({'success': False, 'error': 'All fields are required'}), 400

        try:
            email = data['email'].lower().strip()
            phone_number = data['phone_number']
            password = data['password']

            # Email validation
            if not validate_email(email):
                return jsonify({
                    'success': False,
                    'error': 'Invalid email format. Please use example@domain.com'
                }), 400

            # Phone validation
            if not (1000000000 <= int(phone_number) <= 9999999999):
                return jsonify({'success': False, 'error': 'Invalid phone number'}), 400

            # Check if email exists
            db = Db()
            if db.selectOne("SELECT email FROM customer WHERE email = %s", (email,)):
                return jsonify({'success': False, 'error': 'Email already registered'}), 409

            # Hash password
            hashed_password = hashlib.sha256(password.encode()).hexdigest()

            # Insert new user
            query = """
                INSERT INTO customer 
                (customer_name, email, phone_number, password) 
                VALUES (%s, %s, %s, %s)
            """
            db.insert(query, (
                data['customer_name'].strip(),
                email,
                int(phone_number),
                hashed_password
            ))

            return jsonify({
                'success': True,
                'redirect': url_for('/')  # Ensure you have a route named 'home'
            }), 201

        except IntegrityError as e:
            return jsonify({'success': False, 'error': 'Email or phone already exists'}), 409
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid phone number format'}), 400
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    return render_template('login/signup.html')








if __name__ == '__main__':
    app.run(debug=True)
