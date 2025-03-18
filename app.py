from flask import Flask, render_template, request, redirect, session, jsonify, url_for
from db_connection import Db  # Import the Db class
import os
import bcrypt
import re
from mysql.connector import IntegrityError
import traceback
from flask_socketio import SocketIO
import json

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')
socketio = SocketIO(app)



@app.route('/')
def main():
    return render_template("login/login.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        print("Email received:", email)
        
        try:
            if not email or not password:
                return jsonify({"success": False, "error": "Email and password required"}), 400

            # Determine role and redirect URL
            role = 'Customer'
            redirect_url = url_for('home')
            if '@admin' in email:
                role = 'Admin'
                redirect_url = url_for('admin_home')  # Redirect to admin home
            elif '@staff' in email:
                role = 'Staff'
                redirect_url = url_for('staff')
            elif '@manager' in email:
                role = 'Manager'
                redirect_url = url_for('manager')

            db = Db()
            
            try:
                # Handle admin login separately (only from Admin table)
                if role == 'Admin':
                    admin = db.selectOne(
                        "SELECT admin_id FROM Admin WHERE email = %s AND password = %s",
                        (email, password)
                    )
                    if not admin:
                        return jsonify({"success": False, "error": "Invalid admin credentials"}), 401
                    
                    # Set admin session
                    session.update({
                        'admin_id': admin['admin_id'],
                        'role': 'Admin'
                    })
                    print("Admin login successful. Redirecting to:", redirect_url)  # Debugging
                    return jsonify({
                        "success": True,
                        "redirect": redirect_url
                    })

                # For other roles (Staff, Manager, Customer), check Users table
                user = db.selectOne(
                    "SELECT user_id, password, role FROM Users WHERE email = %s",
                    (email,)
                )
                
                # If user is a staff member, ensure they exist in the Staff table
                if user and user['role'] == 'Staff':
                    staff = db.selectOne(
                        "SELECT staff_id FROM Staff WHERE user_id = %s",
                        (user['user_id'],)
                    )
                    if not staff:
                        return jsonify({"success": False, "error": "Staff record not found"}), 404
                    session['staff_id'] = staff['staff_id']  # Add staff_id to session

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
    # if 'user_id' not in session:
    #     return redirect(url_for('login'))
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





@app.route('/admin')
def admin_home():
    return render_template('admin/index.html')

@app.route('/admin/users')
def admin_users():
    return render_template('admin/pages/users.html')

@app.route('/admin/create_user', methods=['POST'])
def create_user():
    data = request.get_json()
    print("Received data:", data)  # Debugging: Log the received data
    
    # Validation
    if not all(key in data for key in ['username', 'email', 'password', 'role']):
        print("Validation failed: Missing required fields")  # Debugging
        return jsonify({"error": "Missing required fields"}), 400
    
    if data['role'] not in ['Manager', 'Staff', 'Customer']:
        print("Validation failed: Invalid role")  # Debugging
        return jsonify({"error": "Invalid role"}), 400
    
    try:
        # Check if email already exists
        with Db() as db:
            existing_user = db.selectOne("SELECT user_id FROM Users WHERE email = %s", (data['email'],))
            if existing_user:
                print("Validation failed: Email already exists")  # Debugging
                return jsonify({"error": "Email already exists"}), 400
                
        # Insert into Users table
        user_query = """
        INSERT INTO Users (username, email, password, role)
        VALUES (%s, %s, %s, %s)
        """
        user_values = (
            data['username'],
            data['email'],
            data['password'],  # Store password as plain text
            data['role']
        )
        
        with Db() as db:
            user_id = db.insert(user_query, user_values)
            print("User created with ID:", user_id)  # Debugging
            
            # If the user is a manager or staff, insert into respective tables
            if data['role'] == 'Manager':
                manager_query = "INSERT INTO Manager (user_id) VALUES (%s)"
                db.insert(manager_query, (user_id,))
                print("Manager record created")  # Debugging
            elif data['role'] == 'Staff':
                manager_id = get_default_manager_id()
                staff_query = "INSERT INTO Staff (user_id, manager_id) VALUES (%s, %s)"
                db.insert(staff_query, (user_id, manager_id))
                print("Staff record created")  # Debugging
            elif data['role'] == 'Customer':
                customer_query = "INSERT INTO Customer (user_id) VALUES (%s)"
                db.insert(customer_query, (user_id,))
                print("Customer record created")  # Debugging
            
            db.commit()
            return jsonify({"message": "User created successfully"}), 201
    except Exception as e:
        print("Error occurred:", str(e))  # Debugging
        return jsonify({"error": str(e)}), 400

def get_default_manager_id():
    # Implement this function to get a default manager ID
    # This could be the first manager in the system or a specific one
    with Db() as db:
        manager = db.selectOne("SELECT manager_id FROM Manager LIMIT 1")
        return manager['manager_id'] if manager else None



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
    if 'staff_id' not in session:
        return redirect('/login')
    # Pass staff_id to the template
    return render_template("staff/index.html", staff_id=session['staff_id'])

def save_product_to_db(product_data):
    # First, check if category exists
    category_check_query = "SELECT category_id FROM Category WHERE category_name = %s"
    category_insert_query = "INSERT INTO Category (category_name) VALUES (%s)"
    product_insert_query = """
    INSERT INTO Product (product_name, category_id, price, stock_quantity)
    VALUES (%s, %s, %s, %s)
    """
    inventory_log_query = """
    INSERT INTO InventoryLog (product_id, change_type, quantity_changed, staff_id)
    VALUES (%s, 'Added', %s, %s)
    """

    with Db() as db:
        try:
            # Check if category exists
            category = db.selectOne(category_check_query, (product_data['category'],))
            
            if not category:
                # Insert new category
                category_id = db.insert(category_insert_query, (product_data['category'],))
            else:
                category_id = category['category_id']
            
            # Insert product
            product_values = (
                product_data['name'],
                category_id,
                product_data['price'],
                product_data['stock']
            )
            product_id = db.insert(product_insert_query, product_values)
            
            # Log inventory change
            staff_id = session.get('staff_id')
            if not staff_id:
                raise ValueError("Staff ID not found in session")
            
            db.insert(inventory_log_query, (product_id, product_data['stock'], staff_id))
            
            db.commit()
            return product_id
        except Exception as e:
            db.rollback()
            raise e

@socketio.on('add_product')
def handle_add_product(product_data):
    try:
        # Get staff_id from session
        staff_id = session.get('staff_id')
        if not staff_id:
            raise ValueError("Staff ID not found in session")
        
        # Save to database
        product_id = save_product_to_db(product_data)
        
        # Add product_id to the broadcast data
        product_data['product_id'] = product_id
        
        # Broadcast the new product to all connected clients
        socketio.emit('new_product', product_data)
    except Exception as e:
        print(f"Error adding product: {str(e)}")
        socketio.emit('error', {'message': str(e)})

def delete_product_from_db(product_id, staff_id):
    delete_query = "DELETE FROM Product WHERE product_id = %s"
    inventory_log_query = """
    INSERT INTO InventoryLog (product_id, change_type, quantity_changed, staff_id)
    VALUES (%s, 'Removed', 0, %s)
    """

    with Db() as db:
        try:
            # Log the deletion
            db.insert(inventory_log_query, (product_id, staff_id))
            
            # Delete the product
            db.execute(delete_query, (product_id,))
            
            db.commit()
        except Exception as e:
            db.rollback()
            raise e

@socketio.on('delete_product')
def handle_delete_product(data):
    try:
        print("Received delete request:", data)  # Debugging
        product_id = data.get('product_id')
        staff_id = data.get('staff_id')
        
        if not product_id or not staff_id:
            raise ValueError("Product ID and Staff ID are required")
        
        delete_product_from_db(product_id, staff_id)
        
        socketio.emit('product_deleted', {'product_id': product_id})
    except Exception as e:
        print(f"Error deleting product: {str(e)}")
        socketio.emit('error', {'message': str(e)})


@app.route('/logout')
def logout():
    session.clear()  
    return redirect(url_for('login'))


@app.route('/checkout')
def checkout():
    return render_template('home/pages/checkout.html')



if __name__ == '__main__':
    socketio.run(app, debug=True)
