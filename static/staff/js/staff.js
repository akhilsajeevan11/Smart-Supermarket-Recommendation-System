// Initialize Socket.IO
const socket = io();

document.addEventListener("DOMContentLoaded", function () {
    fetchProducts(); // Fetch products when page loads
    socket.on("new_product", (product) => addProductToUI(product));  // Listen for real-time updates
    socket.on("product_deleted", (data) => removeProductFromUI(data.product_id)); // Listen for deletions
    socket.on("new_notification", (data) => handleNewNotification(data)); // Listen for notifications
});

// Fetch all products from backend
function fetchProducts() {
    fetch("/staff/products")
        .then(response => response.json())
        .then(data => {
            window.products = data; // Store products globally
            updateProductList();  // Display products in UI
            checkLowStock();  // Check stock levels
        })
        .catch(error => console.error("Error fetching products:", error));
}

function updateProductList() {
    let tableBody = document.getElementById("product-list");
    tableBody.innerHTML = "";

    if (!window.products || window.products.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="7" class="text-center text-muted">No products added</td></tr>`;
        return;
    }

    tableBody.innerHTML = window.products.map((product) => 
        `<tr>
            <td><img src="${product.image_url}" alt="Product Image" width="50" class="img-thumbnail"></td>
            <td>${product.name}</td>
            <td>${product.category}</td>
            <td>${product.stock}</td>
            <td>${product.promotion ? product.promotion : "-"}</td>
            <td>$${product.price.toFixed(2)}</td>
            <td>
                <button class='btn btn-danger btn-sm' onclick='deleteProduct("${product.product_id}")'>Delete</button>
            </td>
        </tr>`
    ).join("");
}

function addOrUpdateProduct() {
    console.log("Add Product button clicked");  // ✅ Debugging statement

    let name = document.getElementById("product-name").value.trim();
    let category = document.getElementById("category").value;
    let stock = parseInt(document.getElementById("stock-amount").value);
    let promotion = document.getElementById("promotion").value.trim();
    let price = parseFloat(document.getElementById("price").value);
    let imageInput = document.getElementById("product-image").files[0];

    if (!name || isNaN(stock) || stock <= 0 || isNaN(price) || price <= 0) {
        alert("Please enter valid product details.");
        return;
    }

    let formData = new FormData();
    formData.append("name", name);
    formData.append("category", category);
    formData.append("stock", stock);
    formData.append("promotion", promotion);
    formData.append("price", price);
    if (imageInput) {
        formData.append("image", imageInput);
    }

    fetch("/add_product", {
        method: "POST",
        body: formData,
    })
    .then(response => response.json())
    .then(data => {
        console.log("Server response:", data);  // ✅ Debugging statement
        if (data.success) {
            alert("Product added successfully!");
            window.location.reload(); 
            socket.emit("new_product", data.product);  // Emit update to other users
            addProductToUI(data.product); // Update UI dynamically
        } else {
            alert("Failed to add product: " + data.message);
        }
    })
    .catch(error => console.error("Error:", error));
}

// Add a new product dynamically
function addProductToUI(product) {
    window.products.push(product);
    updateProductList();
}

function deleteProduct(product_id) {
    console.log("Deleting product:", product_id);  // ✅ Debugging statement

    fetch(`/delete_product/${product_id}`, { method: "DELETE" })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                removeProductFromUI(product_id);
                socket.emit("product_deleted", { product_id }); // ✅ Emit deletion event
                console.log("Product deleted successfully:", product_id);
            } else {
                console.error("Error deleting product:", data.message);
            }
        })
        .catch(error => console.error("Error:", error));
}

// Remove product from UI
function removeProductFromUI(product_id) {
    window.products = window.products.filter(product => product.product_id !== product_id);
    updateProductList();
}

// Check for low stock products and show alert
function checkLowStock() {
    let lowStockProducts = window.products.filter(product => product.stock < 5);
    let alertBox = document.getElementById("low-stock-alert");

    if (lowStockProducts.length > 0) {
        alertBox.classList.remove("d-none");
        alertBox.innerText = "Low stock on: " + lowStockProducts.map(p => `${p.name} (${p.stock})`).join(", ");
    } else {
        alertBox.classList.add("d-none");
    }
}

// Get staff ID from session
function getStaffId() {
    return window.staffId || "";
}

// Preview image before uploading
function previewImage(event) {
    let preview = document.getElementById("image-preview");
    let file = event.target.files[0];

    if (file) {
        let reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = function (e) {
            preview.src = e.target.result;
            preview.classList.remove("d-none");
        };
    }
}

// Toggle notifications dropdown
function toggleNotifications() {
    let dialog = document.getElementById("notification-dialog");
    dialog.style.display = dialog.style.display === "none" || dialog.style.display === "" ? "block" : "none";
}

// Handle new notifications
function handleNewNotification(data) {
    const notificationList = document.getElementById("notification-list");
    const notificationBadge = document.getElementById("notification-badge");

    // Create a new notification item
    const notificationItem = document.createElement("li");
    notificationItem.className = "list-group-item";
    notificationItem.textContent = `Low stock: ${data.productName} (${data.stockQuantity} left)`;

    // Remove the "No notifications" message if it exists
    if (notificationList.firstElementChild?.classList.contains("text-muted")) {
        notificationList.removeChild(notificationList.firstElementChild);
    }

    // Add the new notification to the top of the list
    notificationList.insertBefore(notificationItem, notificationList.firstChild);

    // Update the notification badge
    const currentCount = parseInt(notificationBadge.textContent) || 0;
    notificationBadge.textContent = currentCount + 1;
    notificationBadge.classList.remove("d-none");
}
