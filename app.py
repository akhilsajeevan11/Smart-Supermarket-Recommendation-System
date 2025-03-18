from flask import Flask, render_template, request, redirect, session, jsonify, url_for, send_from_directory, flash
from db_connection import Db  # Import the Db class
import os
import bcrypt
import re
from mysql.connector import IntegrityError
import traceback
from flask_socketio import SocketIO
import json
from werkzeug.utils import secure_filename
import logging
from datetime import datetime

UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')
socketio = SocketIO(app)

logging.basicConfig(level=logging.INFO)

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)  # Create folder if it does not exist

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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

# @app.route('/home')
# def home():
#     if 'user_id' not in session:
#         return redirect(url_for('login'))
#     return render_template("/home/index.html")


@app.route('/home')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Fetch products from the database
    with Db() as db:
        query = """
            SELECT product_id, product_name, category_id, price, stock_quantity, image_url
            FROM Product
        """
        products = db.select(query)
    
    # Categorize products based on their category
    categorized_products = {
        'Frozen': [],
        'Bakery': [],
        'Dairy & Eggs': [],
        'Beverages': [],
        'Newly Arrived': []
    }
    
    for product in products:
        category_name = get_category_name(product['category_id'])
        if category_name in categorized_products:
            categorized_products[category_name].append(product)
    
    return render_template("/home/index.html", categorized_products=categorized_products)

    # except Exception as e:
    #     print(f"Error fetching products: {e}")
    #     return "Error loading products", 500




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





import os

UPLOAD_FOLDER = "static/uploads"  # Ensure this matches your actual folder path

@app.route("/staff")
def staff():
    if 'staff_id' not in session:  # Check if staff is logged in
        return redirect(url_for('login'))

    try:
        with Db() as db:
            query = """
                SELECT product_id, product_name, category_id, price, stock_quantity, image_url
                FROM Product
            """
            products = db.select(query)

        for product in products:
            filename = product["image_url"].lstrip("/static/uploads/")  # Get the file name
            image_path = os.path.join(UPLOAD_FOLDER, filename)

            # ✅ Verify if the image exists in the folder, else use a default image
            if not os.path.exists(image_path) or not filename:
                product["image_url"] = "/static/uploads/default.jpg"
            else:
                product["image_url"] = f"/static/uploads/{filename}"

        return render_template("staff/index.html", products=products)

    except Exception as e:
        print(f"⚠️ Error fetching products: {e}")
        return "Error loading products", 500







def get_category_name(category_id):
    """Fetch category name from category_id."""
    query = "SELECT category_name FROM Category WHERE category_id = %s"
    with Db() as db:
        result = db.selectOne(query, (category_id,))
    return result["category_name"] if result else "Unknown"

@app.route('/staff/products')
def get_products():
    with Db() as db:
        query = "SELECT product_id, product_name, category_id, price, stock_quantity, image_url FROM Product"
        products = db.select(query)

    def verify_image(image_url):
        filename = image_url.lstrip("/static/uploads/")  # Extract filename
        image_path = os.path.join(UPLOAD_FOLDER, filename)
        return f"/static/uploads/{filename}" if os.path.exists(image_path) else "/static/uploads/default.jpg"

    products_list = [
        {
            "product_id": row["product_id"],
            "name": row["product_name"],
            "category": get_category_name(row["category_id"]),
            "stock": row["stock_quantity"],
            "price": float(row["price"]),
            "image_url": verify_image(row["image_url"])  # ✅ Check and correct image path
        }
        for row in products
    ]

    return jsonify(products_list)





def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_product_to_db(product_data, image_file):
    """Saves product details and image URL to the database."""
    category_check_query = "SELECT category_id FROM Category WHERE category_name = %s"
    category_insert_query = "INSERT INTO Category (category_name) VALUES (%s)"
    product_insert_query = """
    INSERT INTO Product (product_name, category_id, price, stock_quantity, image_url)
    VALUES (%s, %s, %s, %s, %s)
    """

    with Db() as db:
        try:
            # Check if category exists
            category = db.selectOne(category_check_query, (product_data['category'],))
            if not category:
                category_id = db.insert(category_insert_query, (product_data['category'],))
            else:
                category_id = category['category_id']

            # Handle image upload
            image_url = ""
            if image_file and allowed_file(image_file.filename):
                filename = secure_filename(image_file.filename)
                image_path = os.path.join(UPLOAD_FOLDER, filename)
                image_file.save(image_path)
                image_url = f"/{UPLOAD_FOLDER}/{filename}"

            # Insert product
            product_values = (
                product_data['name'],
                category_id,
                float(product_data['price']),
                int(product_data['stock']),
                image_url
            )
            product_id = db.insert(product_insert_query, product_values)
            db.commit()
            return product_id, image_url  # ✅ Return both values correctly
        except Exception as e:
            db.rollback()
            print(f"Error inserting product: {str(e)}")
            return None, None  # ✅ Return None in case of error


@app.route('/add_product', methods=['POST'])
def add_product():
    try:
        product_data = request.form.to_dict()
        image_file = request.files.get('image')  # Ensure image is retrieved

        if not image_file:
            return jsonify({"error": "Image file is required"}), 400

        product_id, image_url = save_product_to_db(product_data, image_file)  # ✅ Fix unpacking

        if product_id is None:
            return jsonify({"success": False, "message": "Failed to add product"}), 500

        product_data['product_id'] = product_id
        product_data['image_url'] = image_url

        # Emit product update to clients
        socketio.emit('new_product', product_data)

        return jsonify({"success": True, "message": "Product added successfully", "product": product_data}), 200

    except Exception as e:
        print(f"Error adding product: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serves uploaded images."""
    return send_from_directory(UPLOAD_FOLDER, filename)

@socketio.on('add_product')
def handle_add_product(data):
    """Handles product addition via WebSocket (without image)."""
    try:
        staff_id = session.get('staff_id')
        if not staff_id:
            raise ValueError("Staff ID not found in session")

        product_id, image_url = save_product_to_db(data, None)  # WebSocket doesn't handle images

        data['product_id'] = product_id
        data['image_url'] = image_url  # Send image URL to frontend

        socketio.emit('new_product', data)
    except Exception as e:
        print(f"Error adding product: {str(e)}")
        socketio.emit('error', {'message': str(e)})



@app.route('/delete_product/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    try:
        with Db() as db:
            db.execute("DELETE FROM Product WHERE product_id = %s", (product_id,))
            db.commit()

        socketio.emit('product_deleted', {'product_id': product_id})  # ✅ WebSocket Emit
        return jsonify({"success": True, "message": "Product deleted"}), 200

    except Exception as e:
        print(f"Error deleting product: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500


@socketio.on('delete_product')
def handle_delete_product(data):
    """Handles product deletion via WebSocket."""
    try:
        product_id = data.get('product_id')
        staff_id = data.get('staff_id')

        if not product_id or not staff_id:
            raise ValueError("Product ID and Staff ID are required")

        delete_product_from_db(product_id, staff_id)
        socketio.emit('product_deleted', {'product_id': product_id})
    except Exception as e:
        print(f"Error deleting product: {str(e)}")
        socketio.emit('error', {'message': str(e)})


def delete_product_from_db(product_id, staff_id):
    """Deletes product from the database and removes its image file."""
    delete_query = "DELETE FROM Product WHERE product_id = %s"
    select_image_query = "SELECT image_url FROM Product WHERE product_id = %s"
    inventory_log_query = """
    INSERT INTO InventoryLog (product_id, change_type, quantity_changed, staff_id)
    VALUES (%s, 'Removed', 0, %s)
    """

    with Db() as db:
        try:
            # ✅ Fetch the product image path before deletion
            db.execute(select_image_query, (product_id,))
            image_result = db.fetchone()

            if image_result and image_result[0]:  # ✅ Ensure image exists
                image_url = image_result[0].strip("/")  # Normalize path
                image_path = os.path.join(UPLOAD_FOLDER, os.path.basename(image_url))

                print(f"🔍 Checking image path: {image_path}")  # Debugging
                if os.path.exists(image_path):  # ✅ Check if file exists before deleting
                    os.remove(image_path)  # ✅ Delete the image file
                    print(f"✅ Image deleted: {image_path}")
                else:
                    print(f"⚠️ Image file not found: {image_path}")

            # ✅ Insert delete log
            db.insert(inventory_log_query, (product_id, staff_id))

            # ✅ Delete product from database
            db.execute(delete_query, (product_id,))
            db.commit()

        except Exception as e:
            db.rollback()
            print(f"❌ Error deleting product: {str(e)}")  # Debugging
            raise e


@app.route('/logout')
def logout():
    """Logs the user out and clears the session."""
    session.clear()
    return redirect(url_for('login'))

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if request.method == 'POST':
        try:
            # 🔹 Step 1: Retrieve JSON data from request
            data = request.get_json()
            customer_email = data.get('email')

            if not customer_email:
                return jsonify({'status': 'error', 'message': 'Email is required!'}), 400

            total_amount = 30.00  # You can dynamically calculate this from cart data

            print(f"✅ Received Checkout Request for: {customer_email}")

            with Db() as db:
                # 🔹 Step 2: Fetch Customer ID
                customer_query = """
                    SELECT customer_id FROM Customer 
                    WHERE user_id = (SELECT user_id FROM Users WHERE email = %s)
                """
                customer = db.selectOne(customer_query, (customer_email,))
                
                if not customer:
                    print("❌ Customer not found!")
                    return jsonify({'status': 'error', 'message': 'Customer not found!'}), 404

                customer_id = customer["customer_id"]
                print(f"✅ Customer ID found: {customer_id}")

                # 🔹 Step 3: Insert Transaction
                transaction_query = """
                    INSERT INTO Transaction (customer_id, total_amount, payment_status, payment_method)
                    VALUES (%s, %s, %s, %s)
                """
                transaction_id = db.insert(transaction_query, (customer_id, total_amount, "Success", "Credit Card"))

                if not transaction_id:
                    print("❌ Transaction insertion failed!")
                    return jsonify({'status': 'error', 'message': 'Transaction could not be created!'}), 500

                print(f"✅ Transaction Created: {transaction_id}")

                # 🔹 Step 4: Insert Purchase Details for Each Product
                cart_items = [
                    {"product_id": 1, "quantity": 2, "price": 15},
                    {"product_id": 2, "quantity": 1, "price": 5},
                    {"product_id": 3, "quantity": 3, "price": 8}
                ]  # Example cart items

                for item in cart_items:
                    sub_total = item["quantity"] * item["price"]
                    purchase_query = """
                        INSERT INTO PurchaseDetail (transaction_id, product_id, quantity, sub_total)
                        VALUES (%s, %s, %s, %s)
                    """
                    db.insert(purchase_query, (transaction_id, item["product_id"], item["quantity"], sub_total))
                    print(f"✅ Purchase Detail Added for Product {item['product_id']}")

                    # 🔹 Step 5: Deduct from Product Stock
                    update_stock_query = """
                        UPDATE Product SET stock_quantity = stock_quantity - %s WHERE product_id = %s
                    """
                    db.execute(update_stock_query, (item["quantity"], item["product_id"]))
                    print(f"✅ Stock Updated for Product {item['product_id']}")

                # 🔹 Step 6: Insert Payment Record
                payment_query = """
                    INSERT INTO Payment (transaction_id, amount, payment_method, payment_status)
                    VALUES (%s, %s, %s, %s)
                """
                db.insert(payment_query, (transaction_id, total_amount, "Credit Card", "Success"))
                print(f"✅ Payment Recorded for Transaction {transaction_id}")

                # 🔹 Step 7: Commit the transaction
                db.commit()
                print("✅ Database Transaction Committed!")

                return jsonify({'status': 'success', 'message': 'Order placed successfully!'})

        except Exception as e:
            db.rollback()
            print(f"❌ Checkout failed: {str(e)}")
            return jsonify({'status': 'error', 'message': f"Checkout failed: {str(e)}"}), 500

    return render_template('home/pages/checkout.html')

if __name__ == '__main__':
    socketio.run(app, debug=True)
