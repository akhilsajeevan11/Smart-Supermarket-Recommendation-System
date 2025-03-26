import os
import pandas as pd
import joblib
from fuzzywuzzy import process
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ✅ Define Windows-Compatible Paths
MODEL_PATH = r"C:\Users\Malavika\Desktop\main project\Smart-Supermarket-Recommendation-System\Model\XGB_Model.joblib"
PRODUCTS_PATH = r"C:\Users\Malavika\Desktop\main project\Smart-Supermarket-Recommendation-System\products.csv"
ORDERS_PATH = r"C:\Users\Malavika\Desktop\main project\Smart-Supermarket-Recommendation-System\orders.csv"

# ✅ Verify File Paths
print(f"Model Path Exists: {os.path.exists(MODEL_PATH)}")
print(f"Products CSV Exists: {os.path.exists(PRODUCTS_PATH)}")
print(f"Orders CSV Exists: {os.path.exists(ORDERS_PATH)}")

# ✅ Load Model with Error Handling
try:
    model = joblib.load(MODEL_PATH)
    print("✅ Model Loaded Successfully!")
except Exception as e:
    print(f"❌ Error loading model: {str(e)}")
    model = None

# ✅ Load Data with Encoding Fallback for Windows
try:
    products = pd.read_csv(PRODUCTS_PATH, encoding="utf-8")
except UnicodeDecodeError:
    products = pd.read_csv(PRODUCTS_PATH, encoding="ISO-8859-1")  # Fallback encoding

try:
    order_products_prior = pd.read_csv(ORDERS_PATH, encoding="utf-8")
except UnicodeDecodeError:
    order_products_prior = pd.read_csv(ORDERS_PATH, encoding="ISO-8859-1")  # Fallback encoding

print(f"✅ Products Loaded: {len(products)} rows")
print(f"✅ Orders Loaded: {len(order_products_prior)} rows")

# ✅ Initialize TF-IDF Vectorizer for Similar Products
if not products.empty and "product_name" in products.columns:
    vectorizer = TfidfVectorizer()
    product_tfidf_matrix = vectorizer.fit_transform(products["product_name"].astype(str))
else:
    vectorizer = None
    product_tfidf_matrix = None

# ✅ Function: Find Complementary Products
def find_complementary_products(product_id, top_n=5):
    """Find complementary products based on co-purchase frequency."""
    if order_products_prior.empty or "product_id" not in order_products_prior.columns:
        return pd.DataFrame()

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

# ✅ Function: Find Similar Products
def find_similar_products(product_name, top_n=5):
    """Find similar products based on TF-IDF content similarity with fuzzy matching."""
    if vectorizer is None or product_tfidf_matrix is None:
        return pd.DataFrame()

    if products.empty or "product_name" not in products.columns:
        return pd.DataFrame()

    # ✅ Normalize case for Windows compatibility
    product_name = product_name.lower()
    products["product_name"] = products["product_name"].astype(str).str.lower()

    # ✅ Use fuzzy matching to find closest match
    fuzzy_result = process.extractOne(product_name, products["product_name"])

    if not fuzzy_result or not isinstance(fuzzy_result, tuple) or len(fuzzy_result) < 2:
        print(f"❌ No valid match found for '{product_name}'")
        return pd.DataFrame()

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

# ✅ Ensure Windows-Compatible Execution
if __name__ == "__main__":
    test_product = "Egg"
    print(find_similar_products(test_product))
