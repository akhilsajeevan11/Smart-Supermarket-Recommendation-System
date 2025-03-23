from flask import Flask, render_template, request, redirect, session, jsonify, url_for, send_from_directory, flash
from db_connection import Db  # Import the Db class
import os
import bcrypt
import re
from mysql.connector import IntegrityError, Error
import traceback
from flask_socketio import SocketIO, emit
import json
from werkzeug.utils import secure_filename
import logging
from datetime import datetime
from dotenv import load_dotenv
import pickle
import uuid
from flask_session import Session
import dill 
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import razorpay




UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

load_dotenv()
# model_path = os.getenv('MODEL_PATH')

# # Load the pre-trained model from the pickle file
# def load_model(model_path):
#     try:
#         with open(model_path, 'rb') as file:
#             model = pickle.load(file)
#         return model
#     except Exception as e:
#         print(f"Error loading model: {str(e)}")
#         return None

# # Load the model
# model = load_model(model_path)  # ✅ Load the model, not just the path

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY') 
socketio = SocketIO(app)


app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)



PRODUCTS_PATH = os.getenv("PRODUCTS_PATH")
ORDERS_PATH = os.getenv("ORDERS_PATH")
PICKLE_PATH = os.getenv("PICKLE_PATH")



# ✅ Load Datasets
try:
    products = pd.read_csv(PRODUCTS_PATH)
    orders = pd.read_csv(ORDERS_PATH)
    print(f"✅ Products Loaded: {len(products)} rows")
    print(f"✅ Orders Loaded: {len(orders)} rows")
except Exception as e:
    print(f"❌ Error loading CSV files: {str(e)}")
    products = pd.DataFrame()
    orders = pd.DataFrame()


# ✅ Load the Pickle File
try:
    with open(PICKLE_PATH, "rb") as file:
        model_data = pickle.load(file)
    print("✅ Model data loaded successfully!")
except Exception as e:
    print(f"❌ Error loading model file: {str(e)}")
    model_data = {}



# ✅ Load the pickle file
try:
    with open("/home/alignminds/Desktop/Akhil/Project/Model/recommendation_system.pkl", "rb") as file:
        model_data = pickle.load(file)

    print("✅ Model data loaded successfully!")

except Exception as e:
    print(f"❌ Error loading model file: {str(e)}")
    model_data = {}

# ✅ Extract components
products = model_data.get("products", pd.DataFrame())
order_products_prior = model_data.get("order_products_prior", pd.DataFrame())
vectorizer = model_data.get("vectorizer", None)
product_tfidf_matrix = model_data.get("product_tfidf_matrix", None)

# ✅ Ensure the model is loaded properly
if "model" in model_data:
    model = model_data["model"]
    print("✅ Recommendation model loaded successfully!")
else:
    print("🚨 Error: Model is missing in the pickle file! Please retrain and save it.")
    model = None  # Prevent errors

# ✅ Function to find complementary products
def find_complementary_products(product_id, top_n=5):
    """Find complementary products based on co-purchase frequency."""
    if order_products_prior.empty:
        return pd.DataFrame()  # Return empty if no order data

    orders_with_product = order_products_prior[order_products_prior['product_id'] == product_id]['order_id'].unique()

    complementary_products = order_products_prior[
        (order_products_prior['order_id'].isin(orders_with_product)) & 
        (order_products_prior['product_id'] != product_id)
    ]

    product_counts = complementary_products['product_id'].value_counts().reset_index()
    product_counts.columns = ['product_id', 'co_occurrence_count']

    top_complementary = product_counts.head(top_n)
    result = top_complementary.merge(products[['product_id', 'product_name']], on='product_id')

    return result[['product_id', 'product_name', 'co_occurrence_count']]

# ✅ Function to find similar products (TF-IDF Content-based)
def find_similar_products(product_name, top_n=5):
    """Find similar products based on TF-IDF content similarity."""
    if vectorizer is None or product_tfidf_matrix is None:
        print("🚨 Vectorizer or TF-IDF matrix is missing!")
        return pd.DataFrame()

    query_vector = vectorizer.transform([product_name])
    cosine_sim = cosine_similarity(query_vector, product_tfidf_matrix).flatten()

    similar_indices = cosine_sim.argsort()[-top_n:][::-1]
    similar_products = products.iloc[similar_indices]

    return similar_products[["product_id", "product_name"]]


# # model_path = os.getenv("MODEL_PATH")

# if not model_path:
#     raise ValueError("MODEL_PATH not found. Check your .env file.")

# model_path="/home/alignminds/Desktop/Akhil/Project/Model/recommendation_system.pkl"

# Load the pre-trained model and functions
# def load_model(model_path):
#     try:
#         with open(model_path, 'rb') as file:
#             model_data = pickle.load(file)
        
#         # Print available keys to check if all components are present
#         print("Loaded model data keys:", model_data.keys())

#         model = model_data.get("model", None)
#         products = model_data.get("products", None)
#         vectorizer = model_data.get("vectorizer", None)
#         find_similar_products = model_data.get("find_similar_products", None)

#         return model, products, vectorizer, find_similar_products

#     except Exception as e:
#         print(f"❌ Error loading model: {str(e)}")
#         return None, None, None, None

# Load everything
# model, products, vectorizer, find_similar_products = load_model(model_path)



razorpay_client = razorpay.Client(auth=(
    os.getenv('RAZORPAY_KEY_ID'),
    os.getenv('RAZORPAY_KEY_SECRET')
))

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
            # Validate email and password
            if not email or not password:
                return jsonify({"success": False, "error": "Email and password required"}), 400

            # Determine role and redirect URL
            role = 'Customer'
            redirect_url = url_for('home')
            if '@admin' in email:
                role = 'Admin'
                redirect_url = url_for('admin_home')
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
                    print("Admin login successful. Redirecting to:", redirect_url)
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

                # If user is a manager, ensure they exist in the Manager table
                if user and user['role'] == 'Manager':
                    manager = db.selectOne(
                        "SELECT manager_id FROM Manager WHERE user_id = %s",
                        (user['user_id'],)
                    )
                    if not manager:
                        return jsonify({"success": False, "error": "Manager record not found"}), 404
                    session['manager_id'] = manager['manager_id']  # Add manager_id to session

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
                            customer = db.selectOne(
                                "SELECT customer_id FROM Customer WHERE user_id = %s",
                                (user['user_id'],)
                            )  # ✅ Fetch newly inserted customer_id
                        session['customer_id'] = customer['customer_id']  # ✅ Store customer_id in session
# Set customer_id in session
                    
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






# ✅ API Endpoint: Get Similar Products
@app.route('/similar_products', methods=['POST'])
def similar_products():
    try:
        data = request.get_json()
        product_name = data.get("product_name")
        print(f"📩 Received request for similar products: {product_name}")

        if not product_name:
            return jsonify({"success": False, "message": "Product name is required"}), 400

        similar_items = find_similar_products(product_name, top_n=5)

        if similar_items.empty:
            print("⚠️ No similar products found!")
            return jsonify({"success": False, "message": "No similar products found"}), 404

        print(f"✅ Similar products found: {similar_items.to_dict(orient='records')}")
        return jsonify({"success": True, "similar_products": similar_items.to_dict(orient="records")})

    except Exception as e:
        print(f"❌ Error in /similar_products: {str(e)}")
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500

# ✅ API Endpoint: Get Complementary Products
@app.route('/complementary_products', methods=['POST'])
def complementary_products():
    try:
        data = request.get_json()
        product_id = data.get("product_id")

        if not product_id:
            return jsonify({"success": False, "message": "Product ID is required"}), 400

        complementary_items = find_complementary_products(product_id, top_n=5)

        if complementary_items.empty:
            return jsonify({"success": False, "message": "No complementary products found"}), 404

        return jsonify({"success": True, "complementary_products": complementary_items.to_dict(orient="records")})

    except Exception as e:
        print(f"❌ Error in /complementary_products: {str(e)}")
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500


# ✅ Function to Find Similar Products by ID (Modified)
def find_similar_products_by_id(product_id, top_n=5):
    """Find similar products based on a product ID using TF-IDF."""
    product_info = products[products["product_id"] == product_id]
    if product_info.empty:
        return []

    product_name = product_info.iloc[0]["product_name"]
    similar_products = find_similar_products(product_name, top_n)

    return similar_products.to_dict(orient="records")


@app.route('/recommend', methods=['POST'])
def recommend():
    try:
        data = request.get_json()
        print(f"📩 Received request data: {data}")

        if not data or "user_id" not in data or "products" not in data:
            return jsonify({"success": False, "message": "Missing required fields (user_id, products)"}), 400

        user_id = data["user_id"]
        product_list = data["products"]  # Expecting a list of product names or IDs

        if not isinstance(product_list, list) or not product_list:
            return jsonify({"success": False, "message": "Products should be a non-empty list"}), 400

        print(f"🔹 User ID: {user_id}, Products: {product_list}")

        product_ids = []
        
        # Check if product_list contains names or IDs
        for product in product_list:
            if isinstance(product, int):  # If product is already an ID
                product_ids.append(product)
            else:  # Search for product by name
                product_info = products[products['product_name'].str.contains(product, case=False, na=False)]
                if not product_info.empty:
                    product_ids.append(product_info.iloc[0]['product_id'])

        if not product_ids:
            return jsonify({"success": False, "message": "No valid product IDs found"}), 404

        print(f"🔹 Found Product IDs: {product_ids}")

        # Collect recommendations for each product in the cart
        all_recommendations = []
        for pid in product_ids:
            similar_items = find_similar_products_by_id(pid, top_n=3)  # Get 3 recommendations per product
            all_recommendations.extend(similar_items)

        # Remove duplicates
        unique_recommendations = {rec["product_id"]: rec for rec in all_recommendations}.values()

        if not unique_recommendations:
            return jsonify({"success": False, "message": "No recommendations found"}), 404

        return jsonify({
            "success": True,
            "recommendations": list(unique_recommendations)
        })

    except Exception as e:
        print(f"❌ Error generating recommendations: {str(e)}")
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500











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
        # print("Productssssss",products)
    
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

def get_category_name(category_id):
    """Fetch category name from category_id."""
    query = "SELECT category_name FROM Category WHERE category_id = %s"
    with Db() as db:
        result = db.selectOne(query, (category_id,))
    return result["category_name"] if result else "Unknown"


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
    # Debugging: Log the request headers
    print("Request headers:", request.headers)
    
    # Debugging: Log the request content type
    print("Content-Type:", request.content_type)
    
    # Debugging: Log the raw request data
    raw_data = request.data
    print("Raw request data:", raw_data)
    
    # Parse JSON data
    try:
        data = request.get_json()  # This is a Python dictionary, not a tuple
        print("Received data:", data)  # Debugging: Log the received data
    except Exception as e:
        print("Error parsing JSON:", str(e))  # Debugging
        return jsonify({"error": "Invalid JSON data"}), 400
    
    # Accessing fields from the dictionary
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')
    
    # Validation
    if not all([username, email, password, role]):
        print("Validation failed: Missing required fields")  # Debugging
        return jsonify({"error": "Missing required fields"}), 400
    
    if role not in ['Manager', 'Staff', 'Customer']:
        print("Validation failed: Invalid role")  # Debugging
        return jsonify({"error": "Invalid role"}), 400
    
    try:
        # Check if email already exists
        with Db() as db:
            existing_user = db.selectOne("SELECT user_id FROM Users WHERE email = %s", (email,))
            if existing_user:
                print("Validation failed: Email already exists")  # Debugging
                return jsonify({"error": "Email already exists"}), 400
                
        # Insert into Users table
        user_query = """
        INSERT INTO Users (username, email, password, role)
        VALUES (%s, %s, %s, %s)
        """
        user_values = (username, email, password, role)
        
        with Db() as db:
            user_id = db.insert(user_query, user_values)
            print("User created with ID:", user_id)  # Debugging
            
            # If the user is a manager or staff, insert into respective tables
            if role == 'Manager':
                manager_query = "INSERT INTO Manager (user_id) VALUES (%s)"
                db.insert(manager_query, (user_id,))
                print("Manager record created")  # Debugging
            elif role == 'Staff':
                manager_id = get_default_manager_id()
                if not manager_id:
                    return jsonify({"error": "No manager found to assign staff"}), 400
                staff_query = "INSERT INTO Staff (user_id, manager_id) VALUES (%s, %s)"
                db.insert(staff_query, (user_id, manager_id))
                print("Staff record created")  # Debugging
            elif role == 'Customer':
                customer_query = "INSERT INTO Customer (user_id) VALUES (%s)"
                db.insert(customer_query, (user_id,))
                print("Customer record created")  # Debugging
            
            db.commit()
            return jsonify({"message": "User created successfully"}), 201
    except Exception as e:
        print("Error occurred:", str(e))  # Debugging
        return jsonify({"error": str(e)}), 500

def get_default_manager_id():
    # Fetch the first manager ID from the Manager table
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

@socketio.on('notify_staff')
def handle_notify_staff(data):
    # Broadcast the notification to all staff
    emit('new_notification', data, broadcast=True)

@app.route('/manager')
def manager():
    if 'manager_id' not in session:  # Check if manager is logged in
        return redirect(url_for('login'))

    try:
        # Fetch products with stock quantity below 10
        low_stock_query = """
        SELECT product_id, product_name, stock_quantity
        FROM Product
        WHERE stock_quantity < 10
        """
        with Db() as db:
            low_stock_products = db.select(low_stock_query)

        # Render the template with low-stock products
        return render_template("manager/index.html", low_stock_products=low_stock_products)

    except Exception as e:
        print(f"Error fetching low-stock products: {str(e)}")
        return render_template("manager/index.html", low_stock_products=[])







UPLOAD_FOLDER = "static/uploads"  # Ensure this matches your actual folder path

@app.route("/send_notification", methods=["POST"])
def send_notification():
    try:
        data = request.get_json()
        product_name = data.get("product_name")
        stock_quantity = data.get("stock_quantity")
        staff_id = data.get("staff_id")

        if not product_name or not stock_quantity or not staff_id:
            return jsonify({"success": False, "message": "Missing required fields"}), 400

        # Insert notification into StockTracking table
        message = f"Low stock alert: {product_name} (Quantity: {stock_quantity})"
        insert_query = """
            INSERT INTO StockTracking (product_name, stock_quantity, message, staff_id)
            VALUES (%s, %s, %s, %s)
        """
        with Db() as db:
            db.execute(insert_query, (product_name, stock_quantity, message, staff_id))
            db.commit()

        return jsonify({"success": True, "message": "Notification sent successfully"})

    except Exception as e:
        print(f"Error sending notification: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500


@app.route("/staff")
def staff():
    if 'staff_id' not in session:  # Check if staff is logged in
        return redirect(url_for('login'))

    try:
        with Db() as db:
            # Fetch products
            product_query = """
                SELECT product_id, product_name, category_id, price, stock_quantity, image_url
                FROM Product
            """
            products = db.select(product_query)

            # Fetch notifications (only the message) from StockTracking table
            notification_query = """
                SELECT message
                FROM StockTracking
                ORDER BY tracking_id DESC
                LIMIT 5
            """
            notifications = db.select(notification_query)
            print(f"Notifications fetched: {notifications}")  # Debugging

        # Process product images
        for product in products:
            filename = product["image_url"].lstrip("/static/uploads/")  # Get the file name
            image_path = os.path.join(UPLOAD_FOLDER, filename)

            # ✅ Verify if the image exists in the folder, else use a default image
            if not os.path.exists(image_path) or not filename:
                product["image_url"] = "/static/uploads/default.jpg"
            else:
                product["image_url"] = f"/static/uploads/{filename}"

        # Render the template with products and notifications
        return render_template("staff/index.html", products=products, notifications=notifications)

    except Exception as e:
        print(f"⚠️ Error fetching products: {e}")
        return "Error loading products", 500









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
    inventory_log_query = """
    INSERT INTO InventoryLog (product_id, change_type, quantity_changed, staff_id)
    VALUES (%s, 'Added', %s, %s)
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

            # Log the addition in InventoryLog
            staff_id = session.get('staff_id')
            if staff_id:
                db.insert(inventory_log_query, (product_id, int(product_data['stock']), staff_id))

            db.commit()
            return product_id, image_url
        except Exception as e:
            db.rollback()
            print(f"Error inserting product: {str(e)}")
            return None, None


@app.route('/add_product', methods=['POST'])
def add_product():
    try:
        product_data = request.form.to_dict()
        image_file = request.files.get('image')  # Ensure image is retrieved

        if not image_file:
            return jsonify({"error": "Image file is required"}), 400

        product_id, image_url = save_product_to_db(product_data, image_file)

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
        staff_id = session.get('staff_id')
        if not staff_id:
            return jsonify({"success": False, "message": "Staff ID not found in session"}), 400

        # ✅ Update the InventoryLog first
        update_response = update_inventory_log(product_id)
        if not update_response.json["success"]:
            return update_response  # Return the error response from update_inventory_log

        # ✅ Delete the product after updating the log
        delete_product_from_db(product_id, staff_id)

        socketio.emit('product_deleted', {'product_id': product_id})  # WebSocket Emit
        return jsonify({"success": True, "message": "Product deleted and inventory log updated"}), 200

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

    with Db() as db:
        try:
            # ✅ Fetch the product image path before deletion
            image_result = db.selectOne(select_image_query, (product_id,))  # Use selectOne instead of fetchone

            if image_result and image_result["image_url"]:  # ✅ Ensure image exists
                image_url = image_result["image_url"].strip("/")  # Normalize path
                image_path = os.path.join(UPLOAD_FOLDER, os.path.basename(image_url))

                print(f"🔍 Checking image path: {image_path}")  # Debugging
                if os.path.exists(image_path):  # ✅ Check if file exists before deleting
                    os.remove(image_path)  # ✅ Delete the image file
                    print(f"✅ Image deleted: {image_path}")
                else:
                    print(f"⚠️ Image file not found: {image_path}")

            # ✅ Delete product from the Product table
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


@app.route('/checkout', methods=['POST'])
def checkout():
    try:
        print("🔍 Session before checkout:", dict(session))  # Debugging

        customer_id = session.get('customer_id')
        if not customer_id:
            print("❌ Checkout error: Customer not logged in")
            return jsonify({"error": "Customer not logged in"}), 401

        data = request.get_json()
        if not data:
            print("❌ Checkout error: No data provided")
            return jsonify({"error": "No data provided"}), 400

        cart_items = data.get('cart_items', [])
        if not cart_items:
            print("❌ Checkout error: Cart is empty")
            return jsonify({"error": "Cart is empty"}), 400

        # ✅ Convert 'price' to 'amount' if necessary
        for item in cart_items:
            if 'price' in item:
                item['amount'] = item.pop('price')

        total_amount = sum(item['amount'] * item['quantity'] for item in cart_items)

        # ✅ Check if session total matches calculated total
        session_total = session.get('total_amount', 0)
        if session_total != total_amount:
            print(f"⚠️ Mismatch: Session total ({session_total}) vs. Calculated total ({total_amount})")
            session['total_amount'] = total_amount  # Sync totals
            session.modified = True

        # ✅ Store data in session
        session['cart_items'] = cart_items
        session.modified = True

        print("✅ Updated session data:", dict(session))  # Debugging

        # ✅ Create a transaction entry
        with Db() as db:
            cursor = db.connection.cursor()
            cursor.execute("""
                INSERT INTO Transaction (customer_id, total_amount, payment_status, payment_method)
                VALUES (%s, %s, 'Pending', 'UPI')
            """, (customer_id, total_amount))

            transaction_id = cursor.lastrowid  # Get the inserted transaction ID
            db.connection.commit()

        print(f"🔗 Proceeding to payment: transaction_id={transaction_id}, total_amount={total_amount}")

        return jsonify({"transaction_id": transaction_id, "total_amount": total_amount})

    except Exception as e:
        print(f"❌ Checkout error: {str(e)}")  # Log exact error
        return jsonify({"error": str(e)}), 500








@app.route('/update_inventory_log/<int:product_id>', methods=['PUT'])
def update_inventory_log(product_id):
    """Updates the change_type in InventoryLog to 'Removed' for the latest entry."""
    try:
        staff_id = session.get('staff_id')
        if not staff_id:
            return jsonify({"success": False, "message": "Staff ID not found in session"}), 400

        # ✅ Find the latest log entry for the product
        find_latest_log_query = """
        SELECT log_id FROM InventoryLog
        WHERE product_id = %s
        ORDER BY change_date DESC
        LIMIT 1
        """

        # ✅ Update the latest log entry
        update_inventory_log_query = """
        UPDATE InventoryLog
        SET change_type = 'Removed'
        WHERE log_id = %s
        """

        with Db() as db:
            # ✅ Find the latest log entry
            latest_log = db.selectOne(find_latest_log_query, (product_id,))
            if not latest_log:
                return jsonify({"success": False, "message": "No log entry found for the product"}), 404

            # ✅ Update the latest log entry
            db.execute(update_inventory_log_query, (latest_log["log_id"],))
            db.commit()

        return jsonify({"success": True, "message": "Inventory log updated successfully"})

    except Exception as e:
        print(f"❌ Error updating inventory log: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

@app.route("/notify_staff", methods=["POST"])
def notify_staff():
    try:
        data = request.get_json()
        product_id = data.get('product_id')  # Get product_id from the request
        product_name = data.get('product_name')
        stock_quantity = data.get('stock_quantity')
        manager_id = session.get('manager_id')  # Get manager_id from the session

        if not manager_id:
            return jsonify({"success": False, "message": "Manager ID not found in session"}), 400

        # Fetch a default staff_id (e.g., the first staff member)
        with Db() as db:
            staff_query = "SELECT staff_id FROM Staff LIMIT 1"
            staff_result = db.selectOne(staff_query)
            if not staff_result:
                return jsonify({"success": False, "message": "No staff found"}), 400

            staff_id = staff_result["staff_id"]

            # Insert into StockTracking table
            insert_query = """
            INSERT INTO StockTracking (product_id, product_name, stock_quantity, message, manager_id, staff_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            message = f"Low stock alert: {product_name} (Product ID: {product_id}, Quantity: {stock_quantity})"
            db.execute(insert_query, (product_id, product_name, stock_quantity, message, manager_id, staff_id))
            db.commit()  # Commit the transaction

        return jsonify({"success": True, "message": "Notification inserted successfully"})

    except Exception as e:
        print(f"Error inserting notification: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500
    

@app.route('/create_order', methods=['POST'])
def create_order():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        customer_id = session.get('customer_id')
        if not customer_id:
            return jsonify({'error': 'Customer not logged in'}), 401

        total_amount = session.get('total_amount', 0)
        payment_method = data.get('payment_method', 'Credit Card')

        if total_amount <= 0:
            return jsonify({'error': 'Invalid total amount'}), 400

        amount = int(float(total_amount) * 100)  # Convert to paise

        with Db() as db:
            cursor = db.connection.cursor()

            # ✅ Check if an existing transaction exists for this customer and amount
            cursor.execute("""
                SELECT transaction_id, payment_status FROM Transaction
                WHERE customer_id = %s AND total_amount = %s
                ORDER BY transaction_id DESC LIMIT 1
            """, (customer_id, total_amount))
            
            existing_transaction = cursor.fetchone()

            if existing_transaction:
                transaction_id = existing_transaction["transaction_id"]
                print(f"✅ Existing transaction found: {transaction_id}")

            else:
                # ✅ Create new transaction if not exists
                cursor.execute("""
                    INSERT INTO Transaction (customer_id, total_amount, payment_status, payment_method)
                    VALUES (%s, %s, 'Pending', %s)
                """, (customer_id, total_amount, payment_method))

                transaction_id = cursor.lastrowid
                db.connection.commit()

                print(f"✅ New transaction created: {transaction_id}")

        # ✅ Create Razorpay Order (only once)
        order = razorpay_client.order.create({
            'amount': amount,
            'currency': 'INR',
            'payment_capture': 1
        })

        razorpay_order_id = order['id']

        return jsonify({'order': order, 'transaction_id': transaction_id, 'payment_method': payment_method}), 200

    except Exception as e:
        print("❌ Create Order Error:", str(e))
        return jsonify({'error': str(e)}), 500

    
@app.route('/payment_verification', methods=['POST'])
def payment_verification():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        required_fields = ['razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature', 'transaction_id', 'payment_method']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        transaction_id = data['transaction_id']
        payment_method = data['payment_method']

        # ✅ Verify Razorpay Signature
        try:
            razorpay_client.utility.verify_payment_signature({
                'razorpay_order_id': data['razorpay_order_id'],
                'razorpay_payment_id': data['razorpay_payment_id'],
                'razorpay_signature': data['razorpay_signature']
            })
        except Exception as e:
            print(f"❌ Razorpay Signature Verification Failed: {str(e)}")
            return jsonify({'error': 'Signature verification failed'}), 400

        with Db() as db:
            cursor = db.connection.cursor()

            # ✅ Ensure transaction exists and is not already marked as Success
            cursor.execute("SELECT payment_status FROM Transaction WHERE transaction_id = %s", (transaction_id,))
            transaction = cursor.fetchone()

            if not transaction:
                return jsonify({'error': 'Invalid transaction ID'}), 400

            if transaction["payment_status"] == "Success":
                return jsonify({'message': 'Payment already verified', 'transaction_id': transaction_id}), 200

            # ✅ Update existing transaction status
            cursor.execute("""
                UPDATE Transaction 
                SET payment_status = 'Success', payment_method = %s
                WHERE transaction_id = %s
            """, (payment_method, transaction_id))

            # ✅ Insert into Payment table
            cursor.execute("""
                INSERT INTO Payment (transaction_id, amount, payment_method, payment_status)
                SELECT transaction_id, total_amount, %s, 'Success'
                FROM Transaction
                WHERE transaction_id = %s
            """, (payment_method, transaction_id))

            db.connection.commit()

        return jsonify({'status': 'success', 'transaction_id': transaction_id}), 200

    except Exception as e:
        print(f"❌ Payment Verification Error: {str(e)}")
        return jsonify({'error': str(e)}), 500




@app.route('/payment')
def payment():
    transaction_id = request.args.get('transaction_id')
    total_amount = request.args.get('total_amount', 0)

    if not transaction_id or transaction_id == "undefined":
        return "Invalid transaction ID", 400  # Ensure transaction ID is valid

    return render_template('payment/payment.html', total_amount=total_amount, transaction_id=transaction_id)

@app.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    try:
        data = request.get_json()
        print("📩 Received Data:", data)  # Debug request payload

        if not data:
            return jsonify({"success": False, "error": "No data received"}), 400

        product_id = str(data.get('product_id'))  # Ensure product_id exists
        product_name = data.get('name', 'Unknown Product')  # Get product name

        if not product_id:
            return jsonify({"success": False, "error": "Missing product_id"}), 400

        customer_id = session.get('customer_id')  # Use session-stored customer_id
        quantity = int(data.get('quantity', 1))  # Default to 1
        amount = int(data.get('amount', data.get('price', 0)))  # Convert price -> amount if needed

        if not customer_id:
            return jsonify({"success": False, "error": "Customer not logged in"}), 401

        # ✅ Store in session
        cart = session.get('cart_items', [])
        cart.append({'product_id': product_id, 'name': product_name, 'quantity': quantity, 'amount': amount})
        session['cart_items'] = cart
        session['total_amount'] = sum(item['amount'] for item in cart)  # Update total
        session.modified = True

        print("✅ Item added to cart successfully:", session['cart_items'])

        # ✅ Fetch recommended products
        recommended_products = find_similar_products(product_name, top_n=5)
        recommended_list = recommended_products.to_dict(orient="records") if not recommended_products.empty else []

        return jsonify({
            "success": True,
            "message": "Item added to cart",
            "recommended_products": recommended_list  # Send recommended products
        })

    except Exception as e:
        print(f"🚨 Error adding to cart: {str(e)}")
        return jsonify({"success": False, "error": "Internal Server Error"}), 500

    


@app.route('/check-session')
def check_session():
    customer_id = session.get('customer_id')
    print(f"🧐 Checking session: customer_id={customer_id}")  # Debugging
    return jsonify({'customer_id': customer_id})


@app.route('/debug-session')
def debug_session():
    return jsonify({
        "user_id": session.get('user_id'),
        "customer_id": session.get('customer_id'),
        "role": session.get('role')
    })


if __name__ == '__main__':
    socketio.run(app, debug=True)
