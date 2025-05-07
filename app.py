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
import joblib
from fuzzywuzzy import process
from datetime import timedelta
import numpy as np
import stripe




UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

load_dotenv()


app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY') 
socketio = SocketIO(app)


# ... existing code ...
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')  # Use environment variable
# ... existing code ...


app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_COOKIE_NAME"] = "user_session"
app.permanent_session_lifetime = timedelta(minutes=30) 
Session(app)



# PRODUCTS_PATH = os.getenv("PRODUCTS_PATH")
# ORDERS_PATH = os.getenv("ORDERS_PATH")
# PICKLE_PATH = os.getenv("PICKLE_PATH")


# ✅ Define Paths
MODEL_PATH = "/home/alignminds/Desktop/Akhil/Project/XGB_Model.joblib"
PRODUCTS_PATH = "/home/alignminds/Desktop/Akhil/Project/Data_set/products.csv"
ORDERS_PATH = "/home/alignminds/Desktop/Akhil/Project/Data_set/orders.csv"


# ✅ Load XGBoost Model (ONLY MODEL)
try:
    model = joblib.load(MODEL_PATH)
    print("Model expects these features:", model.feature_names_in_)
    print("✅ Model Loaded Successfully!")
except Exception as e:
    print(f"❌ Error loading model: {str(e)}")
    model = None


# ✅ Load Products & Orders Data
try:
    products = pd.read_csv(PRODUCTS_PATH)
    order_products_prior = pd.read_csv(ORDERS_PATH)
    print(f"✅ Products Loaded: {len(products)} rows")
    print(f"✅ Orders Loaded: {len(order_products_prior)} rows")
except Exception as e:
    print(f"❌ Error loading CSV files: {str(e)}")
    products = pd.DataFrame()
    order_products_prior = pd.DataFrame()

# ✅ Initialize Vectorizer (TF-IDF) for Similar Products
if not products.empty and "product_name" in products.columns:
    vectorizer = TfidfVectorizer()
    product_tfidf_matrix = vectorizer.fit_transform(products["product_name"])
else:
    vectorizer = None
    product_tfidf_matrix = None





# ✅ Function to Find Complementary Products
def find_complementary_products(product_id, top_n=6):
    """Find complementary products based on co-purchase frequency."""
    if order_products_prior.empty:
        return pd.DataFrame()

    # ✅ Ensure product ID exists
    if product_id not in order_products_prior["product_id"].values:
        return pd.DataFrame()

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




def find_similar_products(product_name, top_n=5):
    """Find similar products based on TF-IDF content similarity with fuzzy matching."""
    if vectorizer is None or product_tfidf_matrix is None:
        return pd.DataFrame()

    if products.empty or "product_name" not in products.columns:
        return pd.DataFrame()

    # ✅ Use fuzzy matching to find closest match
    fuzzy_result = process.extractOne(product_name, products["product_name"])

    # ✅ Ensure valid match was found
    if not fuzzy_result or not isinstance(fuzzy_result, tuple) or len(fuzzy_result) < 2:
        print(f"❌ No valid match found for '{product_name}'")
        return pd.DataFrame()

    # ✅ Safely unpack only first two values
    closest_match, score = fuzzy_result[:2]  
    print(f"🔍 Closest match for '{product_name}': {closest_match} (Score: {score})")

    if score < 70:  # Ignore if match confidence is too low
        print(f"⚠️ Match score too low ({score}) for '{product_name}', returning empty")
        return pd.DataFrame()

    # ✅ Perform similarity search on matched product
    query_vector = vectorizer.transform([closest_match])
    cosine_sim = cosine_similarity(query_vector, product_tfidf_matrix).flatten()
    similar_indices = cosine_sim.argsort()[-top_n:][::-1]
    similar_products = products.iloc[similar_indices]

    return similar_products[["product_id", "product_name"]]





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
    if 'user_id' in session:  # Check if the user is logged in
        return redirect(url_for('home'))  # Redirect to the home page
    return render_template("login/login.html")  # Render the login page


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            data = request.get_json()  # Get JSON data from the request
            if not data:
                return jsonify({"success": False, "error": "No data provided"}), 400

            email = data.get('email', '').strip().lower()
            password = data.get('password', '')
            print("Email received:", email)

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

            print(f"Redirect URL: {redirect_url}")  # Debugging

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
                    print(f"✅ Staff ID set in session: {staff['staff_id']}")  # Debugging

                # If user is a manager, ensure they exist in the Manager table
                if user and user['role'] == 'Manager':
                    manager = db.selectOne(
                        "SELECT manager_id FROM Manager WHERE user_id = %s",
                        (user['user_id'],)
                    )
                    if not manager:
                        return jsonify({"success": False, "error": "Manager record not found"}), 404
                    session['manager_id'] = manager['manager_id']  # Add manager_id to session
                    print(f"✅ Manager ID set in session: {manager['manager_id']}")  # Debugging

                # Validate credentials for all users
                if user and user['password'] == password:
                    session.clear() 
                    session.update({
                        'user_id': user['user_id'],
                        'role': user['role'],
                        'staff_id': staff['staff_id'] if user['role'] == 'Staff' else None,  # ✅ Set staff_id only for staff
                        'manager_id': manager['manager_id'] if user['role'] == 'Manager' else None  # ✅ Set manager_id only for managers
                    })
                    session.modified = True
                    print("Session after login:", dict(session))  # Debugging

                    # ✅ Clear and initialize cart for new login session
                    session['cart_items'] = []
                    session['total_amount'] = 0
                    session.modified = True 
                    
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




@app.route('/sales_data', methods=['GET'])
def get_sales_data():
    try:
        query = """
        SELECT p.product_name, s.total_sales
        FROM SalesAnalytics s
        JOIN Product p ON s.product_id = p.product_id
        ORDER BY s.total_sales DESC
        """

        with Db() as db:
            cursor = db.connection.cursor(dictionary=True)
            cursor.execute(query)
            sales_data = cursor.fetchall()

        return jsonify({"success": True, "sales_data": sales_data})

    except Exception as e:
        print(f"❌ Error fetching sales data: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
 


@app.route('/similar_products', methods=['POST'])
def similar_products():
    try:
        data = request.get_json()
        product_name = data.get("product_name")
        customer_id = session.get("customer_id")
        print(f"📩 Received request for similar products: {product_name}")
        print(f"🔍 Customer ID from session: {customer_id}")  # Debug print

        if not product_name:
            return jsonify({"success": False, "message": "Product name is required"}), 400
        if not customer_id:
            return jsonify({"success": False, "message": "Customer not logged in"}), 401

        # Fetch Similar Products
        similar_items = find_similar_products(product_name, top_n=6)

        if similar_items.empty:
            return jsonify({"success": False, "message": "No similar products found"}), 404

        # Hardcode product details from similar_items
        product_details = []
        recommendation_values = []
        
        with Db() as db:
            cursor = db.connection.cursor(dictionary=True)

            # ✅ Check if the default category exists
            cursor.execute("SELECT category_id FROM Category WHERE category_id = %s", (1,))
            category_exists = cursor.fetchone()

            if not category_exists:
                print("⚠️ Default category does not exist, inserting...")
                cursor.execute("INSERT INTO Category (category_id, category_name) VALUES (%s, %s)", (1, "General"))
                db.connection.commit()
                print("✅ Inserted default category")

            for _, row in similar_items.iterrows():
                # Insert the product into the similar_products table
                cursor.execute("""
                    INSERT INTO similar_products (product_id, product_name, price, stock_quantity, category_id)
                    VALUES (%s, %s, %s, %s, %s)
                """, (row["product_id"], row["product_name"], 50.00, 50, 1))
                print(f"✅ Inserted recommended product into similar_products: {row['product_name']} (ID: {row['product_id']})")

                # Add product details to the response
                product_details.append({
                    "product_id": row["product_id"],
                    "product_name": row["product_name"],
                    "price": 50.00,  # Hardcoded price
                    "stock_quantity": 50  # Hardcoded quantity
                })

                # Add to recommendations
                recommendation_values.append((customer_id, row["product_id"], 'Collaborative'))

            # Insert recommendations
            if recommendation_values:
                cursor.executemany("""
                    INSERT INTO Recommendation (customer_id, product_id, recommendation_type)
                    VALUES (%s, %s, %s)
                """, recommendation_values)

            db.connection.commit()

        return jsonify({
            "success": True,
            "similar_products": product_details
        })

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500




# ✅ API: Find Complementary Products
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
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500

def find_similar_products_by_id(product_id, top_n=5):
    """Find similar products based on a product ID using TF-IDF."""
    product_info = products.loc[products['product_id'] == product_id, 'product_name']
    if product_info.empty:
        return []

    product_name = product_info.values[0]
    similar_products = find_similar_products(product_name, top_n)

    return similar_products.to_dict(orient="records")




# # ✅ Function to Find Similar Products by ID (Modified)
# def find_similar_products_by_id(product_id, top_n=5):
#     """Find similar products based on a product ID using TF-IDF."""
#     product_info = products[products["product_id"] == product_id]
#     if product_info.empty:
#         return []

#     product_name = product_info.iloc[0]["product_name"]
#     similar_products = find_similar_products(product_name, top_n)

#     return similar_products.to_dict(orient="records")


# ✅ API: Recommend Products Based on User's Products
@app.route('/recommend', methods=['POST'])
def recommend():
    try:
        data = request.get_json()

        if not data or "user_id" not in data or "products" not in data:
            return jsonify({"success": False, "message": "Missing required fields (user_id, products)"}), 400

        user_id = data["user_id"]
        product_list = data["products"]  # Expecting a list of product names or IDs

        if not isinstance(product_list, list) or not product_list:
            return jsonify({"success": False, "message": "Products should be a non-empty list"}), 400

        # ✅ Convert product names to product IDs
        product_ids = []
        for product in product_list:
            if isinstance(product, int):  # If product is already an ID
                product_ids.append(product)
            else:  # Search for product by name
                product_info = products[products['product_name'].str.contains(product, case=False, na=False)]
                if not product_info.empty:
                    product_ids.append(product_info.iloc[0]['product_id'])

        if not product_ids:
            return jsonify({"success": False, "message": "No valid product IDs found"}), 404

        # ✅ Collect recommendations
        all_recommendations = []
        for pid in product_ids:
            similar_items = find_similar_products(products.loc[products['product_id'] == pid, 'product_name'].values[0], top_n=3)
            all_recommendations.extend(similar_items.to_dict(orient="records"))

        # ✅ Remove duplicates
        unique_recommendations = {rec["product_id"]: rec for rec in all_recommendations}.values()

        return jsonify({
            "success": True,
            "recommendations": list(unique_recommendations)
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)}), 500











# @app.route('/home')
# def home():
#     if 'user_id' not in session:
#         return redirect(url_for('login'))
    
#     # Fetch products from the database
#     with Db() as db:
#         query = """
#             SELECT product_id, product_name, category_id, price, stock_quantity, image_url
#             FROM Product
#         """
#         products = db.select(query)
#         # print("Productssssss",products)
    
#     # Categorize products based on their category
#     categorized_products = {
#         'Frozen': [],
#         'Bakery': [],
#         'Dairy & Eggs': [],
#         'Beverages': [],
#         'Newly Arrived': []
#     }
    
#     for product in products:
#         category_name = get_category_name(product['category_id'])
#         if category_name in categorized_products:
#             categorized_products[category_name].append(product)
    
#     return render_template("/home/index.html", categorized_products=categorized_products)



@app.route('/home')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']

    with Db() as db:
        # Fetch all products
        query = """
            SELECT product_id, product_name, category_id, price, stock_quantity, image_url
            FROM Product
        """
        products = db.select(query)

        # ✅ Fetch customer's recently purchased products
        purchased_query = """
            SELECT DISTINCT p.product_id, p.product_name, p.category_id, p.price, p.stock_quantity, p.image_url, t.transaction_date
            FROM PurchaseDetail pd
            JOIN Transaction t ON pd.transaction_id = t.transaction_id
            JOIN Product p ON pd.product_id = p.product_id
            WHERE t.customer_id = (
                SELECT customer_id FROM Customer WHERE user_id = %s
            )
            ORDER BY t.transaction_date DESC
            LIMIT 6;
        """
        purchased_products = db.select(purchased_query, (user_id,))

    # Categorize products
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

    return render_template(
        "/home/index.html",
        categorized_products=categorized_products,
        purchased_products=purchased_products
    )



# def get_category_name(category_id):
#     """Fetch category name based on category_id"""
#     with Db() as db:
#         query = "SELECT category_name FROM Category WHERE category_id = %s"
#         result = db.select_one(query, (category_id,))
#         return result['category_name'] if result else "Unknown"




# @app.route("/recommendations", methods=["GET"])
# def top_recommend():
#     """API to get product recommendations for a user."""
#     user_id = request.args.get("user_id", type=int)

#     if not user_id:
#         return jsonify({"error": "Missing user_id"}), 400

#     recommendations = get_top_n_recommendations(user_id)
#     return jsonify({"user_id": user_id, "recommendations": recommendations})

# @app.route('/home')
# def home():
#     if 'user_id' not in session:
#         return redirect(url_for('login'))
    
#     user_id = session['user_id']

#     with Db() as db:
#         # ✅ Fetch available products
#         product_query = """
#             SELECT product_id, product_name, category_id, price, stock_quantity, image_url
#             FROM Product
#         """
#         products = db.select(product_query)

#         # ✅ Fetch purchase history
#         purchase_query = """
#             SELECT t.transaction_id, t.transaction_date AS date, 
#                    t.total_amount, 
#                    GROUP_CONCAT(p.product_name SEPARATOR ', ') AS products
#             FROM Transaction t
#             JOIN PurchaseDetail pd ON t.transaction_id = pd.transaction_id
#             JOIN Product p ON pd.product_id = p.product_id
#             WHERE t.customer_id = %s
#             GROUP BY t.transaction_id, t.transaction_date, t.total_amount
#             ORDER BY t.transaction_date DESC;
#         """
#         purchase_history = db.select(purchase_query, (user_id,))
    
#     # ✅ Categorize products
#     categorized_products = {
#         'Frozen': [],
#         'Bakery': [],
#         'Dairy & Eggs': [],
#         'Beverages': [],
#         'Newly Arrived': []
#     }
    
#     for product in products:
#         category_name = get_category_name(product['category_id'])
#         if category_name in categorized_products:
#             categorized_products[category_name].append(product)
    
#     # ✅ Generate product recommendations
#     recommended_products = get_recommendations(user_id)

#     return render_template(
#         "/home/index.html",
#         categorized_products=categorized_products,
#         purchase_history=purchase_history,
#         recommendations=recommended_products
#     )




# @app.route('/purchase-history', methods=['GET'])
# def get_purchase_history():
#     """Fetch the logged-in user's previous purchases."""
#     user_id = session.get('user_id')
#     if not user_id:
#         return jsonify({"error": "User not logged in"}), 401

#     try:
#         with Db() as db:
#             query = """
#             SELECT t.transaction_id, t.transaction_date AS date, 
#                    t.total_amount, 
#                    GROUP_CONCAT(p.product_name SEPARATOR ', ') AS products
#             FROM Transaction t
#             JOIN PurchaseDetail pd ON t.transaction_id = pd.transaction_id
#             JOIN Product p ON pd.product_id = p.product_id
#             WHERE t.customer_id = %s
#             GROUP BY t.transaction_id, t.transaction_date, t.total_amount
#             ORDER BY t.transaction_date DESC;
#             """
#             purchases = db.select(query, (user_id,))
        
#         return jsonify({"purchases": purchases})

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500












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
    try:
        with Db() as db:
            # Fetch users with roles 'Manager' and 'Staff'
            user_query = """
                SELECT user_id, username, email, role
                FROM Users
                WHERE role IN ('Manager', 'Staff')
                ORDER BY role DESC, username ASC
            """
            users = db.select(user_query)
            print(f"Users fetched: {users}")  # Debugging

        # Render the template with users
        return render_template('admin/index.html', users=users)
    except Exception as e:
        print(f"⚠️ Error fetching users: {e}")
        return "Error loading users", 500

@app.route('/admin/delete_user/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        with Db() as db:
            # Delete the user from the Users table
            delete_query = "DELETE FROM Users WHERE user_id = %s"
            db.execute(delete_query, (user_id,))
            db.commit()
            return jsonify({"success": True, "message": "User deleted successfully"})
    except Exception as e:
        print(f"⚠️ Error deleting user: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


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
        print("⚠️ Manager ID not found in session. Redirecting to login.")  # Debugging
        return redirect(url_for('login'))

    try:
        # Fetch products with stock quantity below 10
        low_stock_query = """
        SELECT product_id, product_name, stock_quantity
        FROM Product
        WHERE stock_quantity < 5 AND stock_quantity > 0
        """
        with Db() as db:
            low_stock_products = db.select(low_stock_query)

        # Render the template with low-stock products
        return render_template("manager/index.html", low_stock_products=low_stock_products)

    except Exception as e:
        print(f"Error fetching low-stock products: {str(e)}")
        return render_template("manager/index.html", low_stock_products=[])




UPLOAD_FOLDER = "static/uploads"  # Ensure this matches your actual folder path



@app.route('/send_notification', methods=['POST'])
def send_notification():
    try:
        data = request.get_json()
        product_name = data.get('product_name')
        stock_quantity = data.get('stock_quantity')
        staff_id = data.get('staff_id')

        print(f"📢 Received notification request: {data}")  # ✅ Debugging

        if not product_name or not stock_quantity:
            return jsonify({"success": False, "message": "Missing required fields"}), 400

        # ✅ Ensure `staff_id` is valid
        if staff_id is None or not str(staff_id).isdigit():
            print("❌ Invalid staff_id received:", staff_id)
            return jsonify({"success": False, "message": "Invalid staff ID"}), 400
        
        staff_id = int(staff_id)  # Convert to integer safely

        message = f"Low stock alert: {product_name} (Quantity: {stock_quantity})"

        with Db() as db:
            db.execute(
                "INSERT INTO StockTracking (product_name, stock_quantity, message, staff_id) VALUES (%s, %s, %s, %s)",
                (product_name, stock_quantity, message, staff_id)
            )
            db.commit()

        # ✅ Emit event for real-time update
        socketio.emit('new_notification', {"message": message})

        print(f"✅ Notification inserted: {message}")  # ✅ Debugging
        return jsonify({"success": True, "message": "Notification sent successfully"})

    except Exception as e:
        print(f"❌ Error sending notification: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500



@app.route("/staff")
def staff():
    # Check if user is logged in and has the role of Staff
    if 'user_id' not in session or session.get('role') != 'Staff':
        print("Unauthorized access to /staff. Redirecting to login.")  # Debugging
        return redirect(url_for('login'))  # Redirect to login page

    try:
        with Db() as db:
            # Fetch products
            product_query = """
                SELECT product_id, product_name, category_id, price, stock_quantity, image_url
                FROM Product
                WHERE stock_quantity > 0
                AND category_id != (SELECT category_id FROM Category WHERE category_name = 'General')
            """
            products = db.select(product_query)
            print(f"Products fetched: {products}")  # Debugging

            # Fetch notifications (as objects with a 'message' key)
            notification_query = """
                SELECT message
                FROM StockTracking
                ORDER BY tracking_id DESC
                LIMIT 5
            """
            notifications = [{"message": n["message"]} for n in db.select(notification_query)]  # ✅ Convert to list of objects
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

        # Render the template with products, notifications, and staff_id
        return render_template(
            "staff/index.html",
            products=products,
            notifications=notifications,  # ✅ Pass notifications as list of objects
            staff_id=session.get('staff_id')  # Pass staff_id to the template
        )

    except Exception as e:
        print(f"⚠️ Error fetching products: {e}")
        return "Error loading products", 500





@app.route('/update_product/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "message": "No data provided"}), 400

        name = data.get('name')
        category = data.get('category')
        stock = data.get('stock')
        price = data.get('price')

        if not name or not category or stock is None or price is None:
            return jsonify({"success": False, "message": "Missing required fields"}), 400

        with Db() as db:
            # Update product in the database
            update_query = """
                UPDATE Product
                SET product_name = %s, category_id = (SELECT category_id FROM Category WHERE category_name = %s),
                    stock_quantity = %s, price = %s
                WHERE product_id = %s
            """
            db.execute(update_query, (name, category, stock, price, product_id))

            # ✅ Remove the product from the StockTracking table
            delete_query = """
                DELETE FROM StockTracking
                WHERE product_id = %s
            """
            db.execute(delete_query, (product_id,))

            db.commit()

        return jsonify({"success": True, "message": "Product updated successfully"}), 200

    except Exception as e:
        print(f"Error updating product: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500





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
    data = request.get_json()
    staff_id = data.get('staff_id')

    if not staff_id:
        return jsonify({"success": False, "message": "Staff ID is missing"}), 400

    try:
        with Db() as db:
            # Check if the product exists
            product = db.selectOne("SELECT * FROM Product WHERE product_id = %s", (product_id,))
            if not product:
                return jsonify({"success": False, "message": "Product not found"}), 404

            # Execute the DELETE operation
            rows_deleted = db.execute("DELETE FROM Product WHERE product_id = %s", (product_id,))
            if rows_deleted == 0:
                return jsonify({"success": False, "message": "Failed to delete product"}), 500

            db.commit()  # ✅ Commit the transaction

        return jsonify({"success": True, "message": "Product deleted successfully"})

    except Exception as e:
        logging.error(f"Error deleting product: {str(e)}")
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
    except ValueError as e:
        print(f"Error deleting product: {str(e)}")
        socketio.emit('error', {'message': str(e)})
    except Exception as e:
        print(f"Error deleting product: {str(e)}")
        socketio.emit('error', {'message': "Internal server error"})


def delete_product_from_db(product_id, staff_id):
    """Deletes product from the database and removes its image file."""
    delete_query = "DELETE FROM Product WHERE product_id = %s"
    select_image_query = "SELECT image_url FROM Product WHERE product_id = %s"

    with Db() as db:
        try:
            # ✅ Check for dependencies in other tables
            cursor = db.connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM Cart WHERE product_id = %s", (product_id,))
            cart_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM PurchaseDetail WHERE product_id = %s", (product_id,))
            purchase_count = cursor.fetchone()[0]

            if cart_count > 0 or purchase_count > 0:
                raise ValueError("Product cannot be deleted as it is referenced in other tables")

            # ✅ Fetch the product image path before deletion
            image_result = db.selectOne(select_image_query, (product_id,))

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
    # Clear the session
    session.pop('user_id', None)
    session.pop('role', None)
    session.pop('customer_id', None)
    session.pop('staff_id', None)
    session.pop('manager_id', None)
    session.pop('admin_id', None)
    session.modified = True
    # Redirect to the login page
    # return redirect(url_for('main'))
    return redirect(url_for('login'))






@app.route('/sales_analytics', methods=['GET'])
def get_sales_analytics():
    try:
        with Db() as db:
            cursor = db.connection.cursor(dictionary=True)
            cursor.execute("""
                SELECT p.product_name, s.total_sales, s.revenue, s.last_sold_date
                FROM SalesAnalytics s
                JOIN Product p ON s.product_id = p.product_id
                ORDER BY s.total_sales DESC
                LIMIT 10
            """)
            sales_data = cursor.fetchall()

        return jsonify({"success": True, "sales_data": sales_data})

    except Exception as e:
        print(f"❌ Error fetching sales analytics: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/future_demand')
def future_demand():
    try:
        # ✅ Fetch trending products from the similar_products table
        query = """
        SELECT 
            sp.product_id AS product_id, 
            sp.product_name, 
            COUNT(r.product_id) AS recommendation_count,  # Number of times the product was recommended
            (COUNT(r.product_id) * 1.0) AS demand_score  # Demand score based on recommendation count
        FROM Recommendation r
        JOIN similar_products sp ON r.product_id = sp.product_id
        WHERE r.recommendation_type = 'Collaborative'
        GROUP BY sp.product_id, sp.product_name
        ORDER BY demand_score DESC
        LIMIT 10;  # Limit to top 10 trending products
        """

        with Db() as db:
            data = db.select(query)
            
        if not data:
            print("⚠️ No future demand data found. Fetching default products from similar_products table.")
            # Fallback: Fetch default products from similar_products table
            fallback_query = """
            SELECT product_id, product_name
            FROM similar_products
            LIMIT 10;
            """
            data = db.select(fallback_query)
            if not data:
                return jsonify({"success": True, "future_demand": [], "message": "No trending products found."})
        
        return jsonify({"success": True, "future_demand": data})
    
    except Exception as e:
        print(f"❌ Future Demand Fetch Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500




@app.route('/customer_preferences', methods=['GET'])
def customer_preferences():
    try:
        query = """
        SELECT p.product_name, SUM(c.quantity) as total_quantity
        FROM Cart c
        JOIN Product p ON c.product_id = p.product_id
        GROUP BY p.product_name
        ORDER BY total_quantity DESC
        LIMIT 5  -- Get Top 5 preferred products
        """

        # ✅ Use Db() context manager
        with Db() as db:
            preferences = db.select(query)  # ✅ Assuming 'select()' method exists in Db class

        return jsonify({"success": True, "customer_preferences": preferences})  # ✅ Direct return

    except Exception as e:
        print(f"❌ Customer Preferences Fetch Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500







def update_sales_analytics(transaction_id):
    try:
        with Db() as db:
            cursor = db.connection.cursor()

            # 🔍 Get all purchased products for this transaction
            cursor.execute("""
                SELECT product_id, quantity, sub_total
                FROM PurchaseDetail
                WHERE transaction_id = %s
            """, (transaction_id,))
            purchases = cursor.fetchall()

            if not purchases:
                print(f"⚠️ No purchase details found for transaction {transaction_id}")
                return

            for item in purchases:
                product_id, quantity, sub_total = item

                # ✅ Check if product exists in SalesAnalytics
                cursor.execute("""
                    SELECT total_sales, revenue FROM SalesAnalytics WHERE product_id = %s
                """, (product_id,))
                analytics_entry = cursor.fetchone()

                if analytics_entry:
                    # 🔄 Update existing record
                    total_sales = analytics_entry[0] + quantity
                    revenue = analytics_entry[1] + sub_total

                    cursor.execute("""
                        UPDATE SalesAnalytics
                        SET total_sales = %s, revenue = %s, last_sold_date = NOW()
                        WHERE product_id = %s
                    """, (total_sales, revenue, product_id))
                    print(f"✅ Updated SalesAnalytics for product {product_id}")

                else:
                    # ➕ Insert new record
                    cursor.execute("""
                        INSERT INTO SalesAnalytics (product_id, total_sales, revenue, last_sold_date)
                        VALUES (%s, %s, %s, NOW())
                    """, (product_id, quantity, sub_total))
                    print(f"✅ Inserted new SalesAnalytics for product {product_id}")

            db.connection.commit()
            print("✅ Sales analytics updated successfully!")

    except Exception as e:
        print(f"❌ Error updating sales analytics: {str(e)}")



@app.route('/update_inventory_log/<int:product_id>', methods=['PUT'])
def update_inventory_log(product_id):
    """Updates the change_type in InventoryLog to 'Removed' for the latest entry."""
    try:
        staff_id = session.get('staff_id')
        if not staff_id:
            print("⚠️ Staff ID not found in session")  # Debugging
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
                print(f"⚠️ No log entry found for product {product_id}")  # Debugging
                return jsonify({"success": False, "message": "No log entry found for the product"}), 404

            # ✅ Update the latest log entry
            db.execute(update_inventory_log_query, (latest_log["log_id"],))
            db.commit()
            print(f"✅ Inventory log updated for product {product_id}")  # Debugging

        return jsonify({"success": True, "message": "Inventory log updated successfully"})

    except Exception as e:
        print(f"❌ Error updating inventory log: {str(e)}")  # Debugging
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

        with Db() as db:
            cursor = db.connection.cursor()

            # ✅ Create a transaction entry
            cursor.execute("""
                INSERT INTO Transaction (customer_id, total_amount, payment_status, payment_method)
                VALUES (%s, %s, 'Pending', 'Credit Card')
            """, (customer_id, total_amount))

            transaction_id = cursor.lastrowid
            db.connection.commit()

            # ✅ Insert cart items into the Cart table
            for item in cart_items:
                # Check if the product exists in the Product table or similar_products table
                cursor.execute("""
                    SELECT product_id FROM Product WHERE product_id = %s
                    UNION
                    SELECT product_id FROM similar_products WHERE product_id = %s
                """, (item["product_id"], item["product_id"]))
                product_exists = cursor.fetchone()

                if not product_exists:
                    print(f"❌ Product not found in Product or similar_products table: {item['product_id']}")
                    return jsonify({"error": f"Product not found: {item['product_id']}"}), 400

                # Insert into Cart table
                cursor.execute("""
                    INSERT INTO Cart (customer_id, product_id, quantity, amount)
                    VALUES (%s, %s, %s, %s)
                """, (customer_id, item["product_id"], item["quantity"], item["amount"] * item["quantity"]))

            # ✅ Insert purchase details and update stock quantity
            for item in cart_items:
                # Skip stock deduction for recommended products
                if item.get("is_recommended"):
                    print(f"⚠️ Skipping stock deduction for recommended product: {item['name']}")
                    continue

                # Check if stock quantity is sufficient (only for products in the Product table)
                cursor.execute("""
                    SELECT stock_quantity FROM Product WHERE product_id = %s
                """, (item["product_id"],))
                stock_quantity = cursor.fetchone()

                if not stock_quantity:
                    print(f"⚠️ Skipping stock check for recommended product: {item['name']}")
                    continue

                if stock_quantity[0] < item["quantity"]:
                    print(f"❌ Insufficient stock for product_id={item['product_id']}")
                    return jsonify({"error": f"Insufficient stock for product {item['name']}"}), 400

                # Insert purchase details
                cursor.execute("""
                    INSERT INTO PurchaseDetail (transaction_id, product_id, quantity, sub_total)
                    VALUES (%s, %s, %s, %s)
                """, (transaction_id, item["product_id"], item["quantity"], item["amount"] * item["quantity"]))

                # Update stock quantity in the Product table (only for products in the Product table)
                cursor.execute("""
                    UPDATE Product
                    SET stock_quantity = stock_quantity - %s
                    WHERE product_id = %s
                """, (item["quantity"], item["product_id"]))

            db.connection.commit()

        print(f"🔗 Proceeding to payment: transaction_id={transaction_id}, total_amount={total_amount}")

        # ✅ Update Sales Analytics
        update_sales_analytics(transaction_id)

        return jsonify({"transaction_id": transaction_id, "total_amount": total_amount})

    except Exception as e:
        print(f"❌ Checkout error: {str(e)}")  # Log exact error
        return jsonify({"error": str(e)}), 500






@app.route('/payment')
def payment():
    transaction_id = request.args.get('transaction_id')
    total_amount = request.args.get('total_amount', 0)

    if not transaction_id or transaction_id == "undefined":
        return "Invalid transaction ID", 400  # Ensure transaction ID is valid

    return render_template('payment/payment.html', total_amount=total_amount, transaction_id=transaction_id)





# @app.route('/create_order', methods=['POST'])
# def create_order():
#     try:
#         data = request.json
#         if not data:
#             return jsonify({'error': 'No data provided'}), 400

#         customer_id = session.get('customer_id')
#         if not customer_id:
#             return jsonify({'error': 'Customer not logged in'}), 401

#         total_amount = session.get('total_amount', 0)
#         payment_method = data.get('payment_method', 'Credit Card')

#         if total_amount <= 0:
#             return jsonify({'error': 'Invalid total amount'}), 400

#         amount = int(float(total_amount) * 100)  # Convert to paise

#         with Db() as db:
#             cursor = db.connection.cursor(dictionary=True)  # ✅ Ensure dictionary output

#             # ✅ Check if an existing transaction exists for this customer and amount
#             cursor.execute("""
#                 SELECT transaction_id, payment_status FROM Transaction
#                 WHERE customer_id = %s AND total_amount = %s
#                 ORDER BY transaction_id DESC LIMIT 1
#             """, (customer_id, total_amount))
            
#             existing_transaction = cursor.fetchone()

#             if existing_transaction:
#                 # ✅ Ensure data is retrieved as a dictionary
#                 if isinstance(existing_transaction, dict):
#                     transaction_id = existing_transaction["transaction_id"]
#                     print(f"✅ Existing transaction found: {transaction_id}")
#                 else:
#                     return jsonify({'error': 'Database response format error'}), 500

#             else:
#                 # ✅ Create new transaction if not exists
#                 cursor.execute("""
#                     INSERT INTO Transaction (customer_id, total_amount, payment_status, payment_method)
#                     VALUES (%s, %s, 'Pending', %s)
#                 """, (customer_id, total_amount, payment_method))

#                 transaction_id = cursor.lastrowid
#                 db.connection.commit()

#                 print(f"✅ New transaction created: {transaction_id}")

#         # ✅ Create Razorpay Order (only once)
#         order = razorpay_client.order.create({
#             'amount': amount,
#             'currency': 'INR',
#             'payment_capture': 1
#         })

#         razorpay_order_id = order['id']

#         return jsonify({'order': order, 'transaction_id': transaction_id, 'payment_method': payment_method}), 200

#     except Exception as e:
#         print("❌ Create Order Error:", str(e))
#         return jsonify({'error': str(e)}), 500




# @app.route('/payment_verification', methods=['POST'])
# def payment_verification():
#     try:
#         data = request.json
#         if not data:
#             return jsonify({'error': 'No data provided'}), 400

#         required_fields = ['razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature', 'transaction_id', 'payment_method']
#         for field in required_fields:
#             if field not in data:
#                 return jsonify({'error': f'Missing required field: {field}'}), 400

#         transaction_id = data['transaction_id']
#         payment_method = data['payment_method']

#         # ✅ Verify Razorpay Signature
#         try:
#             razorpay_client.utility.verify_payment_signature({
#                 'razorpay_order_id': data['razorpay_order_id'],
#                 'razorpay_payment_id': data['razorpay_payment_id'],
#                 'razorpay_signature': data['razorpay_signature']
#             })
#         except Exception as e:
#             print(f"❌ Razorpay Signature Verification Failed: {str(e)}")
#             return jsonify({'error': 'Signature verification failed'}), 400

#         with Db() as db:
#             cursor = db.connection.cursor(dictionary=True)  # ✅ Ensure dictionary output

#             # ✅ Ensure transaction exists and is not already marked as Success
#             cursor.execute("SELECT payment_status FROM Transaction WHERE transaction_id = %s", (transaction_id,))
#             transaction = cursor.fetchone()

#             if not transaction:
#                 return jsonify({'error': 'Invalid transaction ID'}), 400

#             if transaction["payment_status"] == "Success":  # ✅ Use dictionary key
#                 return jsonify({'message': 'Payment already verified', 'transaction_id': transaction_id}), 200

#             # ✅ Update existing transaction status
#             cursor.execute("""
#                 UPDATE Transaction 
#                 SET payment_status = 'Success', payment_method = %s
#                 WHERE transaction_id = %s
#             """, (payment_method, transaction_id))

#             # ✅ Insert into Payment table
#             cursor.execute("""
#                 INSERT INTO Payment (transaction_id, amount, payment_method, payment_status)
#                 SELECT transaction_id, total_amount, %s, 'Success'
#                 FROM Transaction
#                 WHERE transaction_id = %s
#             """, (payment_method, transaction_id))

#             db.connection.commit()

#         return jsonify({'status': 'success', 'transaction_id': transaction_id}), 200

#     except Exception as e:
#         print(f"❌ Payment Verification Error: {str(e)}")
#         return jsonify({'error': str(e)}), 500











@app.route('/payment_verification', methods=['POST'])
def payment_verification():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        required_fields = ['stripe_session_id', 'transaction_id', 'payment_method']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        transaction_id = data['transaction_id']
        payment_method = data['payment_method']
        stripe_session_id = data['stripe_session_id']

        # ✅ Verify Stripe Payment
        try:
            # Retrieve the Stripe session
            stripe_session = stripe.checkout.Session.retrieve(stripe_session_id)
            
            # Retrieve the payment intent
            payment_intent = stripe.PaymentIntent.retrieve(stripe_session.payment_intent)

            if payment_intent.status != 'succeeded':
                return jsonify({'error': 'Payment not successful'}), 400
        except Exception as e:
            print(f"❌ Stripe Payment Verification Failed: {str(e)}")
            return jsonify({'error': 'Payment verification failed'}), 400

        with Db() as db:
            cursor = db.connection.cursor(dictionary=True)

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
                SET payment_status = 'Success', 
                    payment_method = %s,
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

        return jsonify({
            'status': 'success', 
            'transaction_id': transaction_id,
        }), 200

    except Exception as e:
        print(f"❌ Payment Verification Error: {str(e)}")
        return jsonify({'error': str(e)}), 500



@app.route('/create_stripe_session', methods=['POST'])
def create_stripe_session():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        transaction_id = data.get('transaction_id')
        total_amount = data.get('total_amount')
        payment_method = data.get('payment_method')

        if not all([transaction_id, total_amount, payment_method]):
            return jsonify({"error": "Missing required fields"}), 400

        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'inr',
                    'product_data': {
                        'name': f'Payment for Transaction {transaction_id}'
                    },
                    'unit_amount': int(float(total_amount) * 100),
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=url_for('payment_success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for('payment', _external=True, transaction_id=transaction_id, total_amount=total_amount),
            metadata={
                'transaction_id': transaction_id,
                'payment_method': payment_method
            }
        )

        return jsonify({"id": session.id})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/payment_success')
def payment_success():
    session_id = request.args.get('session_id')
    if not session_id:
        return "Missing session_id", 400

    try:
        # Retrieve the checkout session
        checkout_session = stripe.checkout.Session.retrieve(session_id)
        
        # Retrieve the payment intent
        payment_intent = stripe.PaymentIntent.retrieve(checkout_session.payment_intent)

        if payment_intent.status != 'succeeded':
            return "Payment not successful", 400

        # Get the original transaction ID and payment method from the session metadata
        transaction_id = checkout_session.metadata.get('transaction_id')
        payment_method = checkout_session.metadata.get('payment_method')
        if not transaction_id or not payment_method:
            return "Missing transaction ID or payment method in session metadata", 400

        amount = payment_intent.amount_received / 100  # Convert to dollars
        payment_intent_id = payment_intent.id

        # Save to DB
        with Db() as db:
            cursor = db.connection.cursor()

            # Check if payment_intent_id column exists
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_NAME = 'Transaction' 
                AND COLUMN_NAME = 'payment_intent_id'
            """)
            has_payment_intent_column = cursor.fetchone() is not None

            # Update the transaction with payment details
            if has_payment_intent_column:
                update_query = """
                    UPDATE Transaction
                    SET payment_status = 'Success', 
                        payment_method = %s,
                        payment_intent_id = %s
                    WHERE transaction_id = %s
                """
                cursor.execute(update_query, (payment_method, payment_intent_id, transaction_id))
            else:
                update_query = """
                    UPDATE Transaction
                    SET payment_status = 'Success', 
                        payment_method = %s
                    WHERE transaction_id = %s
                """
                cursor.execute(update_query, (payment_method, transaction_id))

            # Insert into Payment table
            if has_payment_intent_column:
                insert_query = """
                    INSERT INTO Payment (transaction_id, amount, payment_method, payment_status, payment_intent_id)
                    VALUES (%s, %s, %s, 'Success', %s)
                """
                cursor.execute(insert_query, (transaction_id, amount, payment_method, payment_intent_id))
            else:
                insert_query = """
                    INSERT INTO Payment (transaction_id, amount, payment_method, payment_status)
                    VALUES (%s, %s, %s, 'Success')
                """
                cursor.execute(insert_query, (transaction_id, amount, payment_method))

            db.connection.commit()

        # Clear cart from session
        session.pop('cart_items', None)

        # Return a confirmation page or redirect with a success message
        return render_template('payment/payment_success.html', transaction_id=transaction_id)

    except Exception as e:
        print(f"❌ Error verifying payment: {str(e)}")
        return "Payment verification failed", 500








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

    

    


# @app.route('/check-session')
# def check_session():
#     customer_id = session.get('customer_id')
#     print(f"🧐 Checking session: customer_id={customer_id}")  # Debugging
#     return jsonify({'customer_id': customer_id})


@app.route('/check-session')
def check_session():
    # Check if the user is logged in
    logged_in = 'user_id' in session
    return jsonify({'loggedIn': logged_in})


@app.route('/debug-session')
def debug_session():
    return jsonify({
        "user_id": session.get('user_id'),
        "customer_id": session.get('customer_id'),
        "role": session.get('role')
    })

@app.route('/protected')
def protected():
    if 'user_id' not in session:
        return redirect(url_for(''))
    return "This is a protected page."

@app.after_request
def add_cache_control(response):
    # Add headers to prevent caching
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response






# def get_user_purchase_history(customer_id):
#     """Fetch the user's past purchases from the database."""
#     with Db() as db:
#         purchase_query = """
#         SELECT DISTINCT pd.product_id, p.product_name
#         FROM PurchaseDetail pd
#         JOIN Transaction t ON pd.transaction_id = t.transaction_id
#         JOIN Product p ON pd.product_id = p.product_id
#         WHERE t.customer_id = %s
#         """
#         purchased_products = db.select(purchase_query, (customer_id,))
    
#     return purchased_products


# def prepare_features(customer_id):
#     with Db() as db:
#         # ✅ Fetch user transaction history
#         user_query = """
#             SELECT COUNT(transaction_id) AS total_orders, 
#                    AVG(DATEDIFF(NOW(), transaction_date)) AS avg_days_since_prior_order
#             FROM Transaction
#             WHERE customer_id = %s
#         """
#         user_features = db.selectOne(user_query, (customer_id,))

#         # 🔍 Ensure user has past transactions
#         if not user_features or not user_features["total_orders"]:
#             return None  

#         # ✅ Fetch purchased product IDs
#         purchase_query = """
#             SELECT DISTINCT product_id
#             FROM PurchaseDetail
#             WHERE transaction_id IN (
#                 SELECT transaction_id FROM Transaction WHERE customer_id = %s
#             )
#         """
#         purchased_products = db.select(purchase_query, (customer_id,))

#         product_ids = [p["product_id"] for p in purchased_products]
#         if not product_ids:
#             return None  

#         # ✅ Fetch product-related data
#         placeholders = ",".join(["%s"] * len(product_ids))
#         product_query = f"""
#             SELECT product_id, AVG(reordered) AS product_reorder_rate
#             FROM PurchaseDetail
#             WHERE product_id IN ({placeholders})
#             GROUP BY product_id
#         """

#         product_features = db.select(product_query, tuple(product_ids))

#     # Convert to DataFrame
#     feature_data = pd.DataFrame(product_features)

#     # ✅ Ensure all required columns exist
#     feature_data["user_id"] = customer_id
#     feature_data["user_product_interaction"] = 1  
#     feature_data["total_orders"] = user_features["total_orders"]
#     feature_data["avg_days_since_prior_order"] = user_features["avg_days_since_prior_order"]

#     # Fill missing columns
#     required_columns = ["user_id", "user_product_interaction", "total_orders", "avg_days_since_prior_order", "product_reorder_rate"]
#     for col in required_columns:
#         if col not in feature_data:
#             feature_data[col] = 0  

#     return feature_data


# def recommend_products(customer_id, top_n=5):
#     """Generate top-N recommendations for a user."""
#     feature_data = prepare_features(customer_id)

#     if feature_data is None:
#         return []  

#     # ✅ Ensure product_id exists before predicting
#     if "product_id" not in feature_data.columns:
#         return []

#     # ✅ Generate recommendations
#     feature_data["predicted_score"] = model.predict_proba(
#         feature_data.drop(columns=["product_id"], errors="ignore")
#     )[:, 1]
    
#     top_recommendations = feature_data.sort_values(by="predicted_score", ascending=False).head(top_n)
#     recommended_product_ids = top_recommendations["product_id"].tolist()

#     # ✅ Fetch product details
#     with Db() as db:
#         placeholders = ",".join(["%s"] * len(recommended_product_ids))
#         product_query = f"""
#             SELECT product_id, product_name, price, image_url 
#             FROM Product 
#             WHERE product_id IN ({placeholders})
#         """
#         recommended_products = db.select(product_query, tuple(recommended_product_ids))

#     return recommended_products


# @app.route('/get_recommendations', methods=['GET'])
# def get_recommendations():
#     try:
#         customer_id = session.get('customer_id')
#         if not customer_id:
#             return jsonify({"success": False, "message": "Customer not logged in"}), 401

#         recommended_products = recommend_products(customer_id)

#         return jsonify({
#             "success": True,
#             "recommended_products": recommended_products
#         })

#     except Exception as e:
#         print(f"❌ Error in /get_recommendations: {str(e)}")
#         traceback.print_exc()
#         return jsonify({"success": False, "message": str(e)}), 500


# # ✅ Get Recommendations
# def get_top_n_recommendations(user_id, n=5):
#     """Fetch recommendations for a given user."""
#     with Db() as db:
#         # ✅ Fetch user and product features from the database
#         query = """
#         SELECT user_id, product_id, user_product_interaction, total_orders, product_reorder_rate
#         FROM PurchaseDetail
#         JOIN Transaction ON PurchaseDetail.transaction_id = Transaction.transaction_id
#         WHERE Transaction.customer_id = %s
#         """
#         df = db.select(query, (user_id,))
#         df = pd.DataFrame(df)

#         if df.empty:
#             return []

#         # ✅ Predict probabilities
#         df["predicted_score"] = model.predict_proba(df.drop(columns=["user_id", "product_id"]))[:, 1]

#         # ✅ Return top N recommendations
#         top_n = df.sort_values(by="predicted_score", ascending=False).head(n)
#         return top_n[["product_id", "predicted_score"]].to_dict(orient="records")



if __name__ == '__main__':
    socketio.run(app, debug=True)
