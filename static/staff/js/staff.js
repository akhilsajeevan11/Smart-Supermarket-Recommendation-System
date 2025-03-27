// Initialize Socket.IO
const socket = io();

// Store notifications in a global array
let notifications = [];

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
    console.log("Add Product button clicked");  // ✅ Debugging

    let name = document.getElementById("product-name")?.value.trim();
    let category = document.getElementById("category")?.value;
    let stock = parseInt(document.getElementById("stock-amount")?.value);
    let promotion = document.getElementById("promotion")?.value.trim();
    let price = parseFloat(document.getElementById("price")?.value);
    let imageInput = document.getElementById("product-image")?.files[0];

    console.log("Form values:", { name, category, stock, promotion, price, imageInput });  // ✅ Debugging

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

    console.log("FormData:", formData);  // ✅ Debugging

    fetch("/add_product", {
        method: "POST",
        body: formData,
    })
    .then(response => response.json())
    .then(data => {
        console.log("Server response:", data);  // ✅ Debugging
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
    const staffId = getStaffId(); // Get staff ID from session
    if (!staffId) {
        console.error("Staff ID not found. Cannot delete product.");
        alert("Staff ID not found. Please log in again.");
        return;
    }

    fetch(`/delete_product/${product_id}`, {
        method: "DELETE",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ staff_id: staffId }) // Include staff_id in the request
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            removeProductFromUI(product_id);
            socket.emit("product_deleted", { product_id });
            window.location.reload();
            console.log("Product deleted successfully:", product_id);
        } else {
            console.error("Error deleting product:", data.message);
            alert("Error deleting product: " + data.message);
        }
    })
    .catch(error => console.error("Error:", error));
}

// Remove product from UI
function removeProductFromUI(product_id) {
    window.products = window.products.filter(product => product.product_id !== product_id);
    updateProductList();
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

document.addEventListener("DOMContentLoaded", function () {
    fetchProducts();
    
    socket.on("new_notification", (data) => {
        handleNewNotification(data);
    });
});

// Toggle Notifications List
function toggleNotifications() {
    const dialog = document.getElementById("notification-dialog");
    dialog.style.display = dialog.style.display === "none" || dialog.style.display === "" ? "block" : "none";

    updateNotificationUI(); // Refresh notification UI when opened
}

// Handle New Notifications
function handleNewNotification(data) {
    const notificationBadge = document.getElementById("notification-badge");
    notifications.unshift(data); // Add new notification to the top

    updateNotificationUI(); // Refresh UI

    // Update notification badge count
    notificationBadge.textContent = notifications.length;
    notificationBadge.classList.remove("d-none");
}

// Update the UI with notifications
function updateNotificationUI() {
    const notificationList = document.getElementById("notification-list");
    notificationList.innerHTML = "";

    if (notifications.length === 0) {
        notificationList.innerHTML = `<li class="list-group-item text-muted">No notifications</li>`;
        return;
    }

    notifications.forEach(notification => {
        const notificationItem = document.createElement("li");
        notificationItem.className = "list-group-item";
        notificationItem.textContent = notification.message;
        notificationList.appendChild(notificationItem);
    });
}

// Simulate a test notification when button is clicked (For debugging)
function testNotification() {
    handleNewNotification({ message: "🔔 Test Notification at " + new Date().toLocaleTimeString() });
}


function sendNotification(productName, stock) {
    // Check if the same notification already exists
    const existingNotification = notifications.find(n => n.message.includes(productName));
    if (existingNotification) return; // Avoid duplicates

    console.log(`🔔 Low stock alert: ${productName} has only ${stock} left.`);

    handleNewNotification({
        message: `⚠️ Low stock: ${productName} (Only ${stock} left)`,
    });
}



// Check for low-stock products and send notifications
function checkLowStock() {
    if (!window.products || window.products.length === 0) return;

    const lowStockProducts = window.products.filter(product => product.stock > 0 && product.stock < 10);
    const staffId = getStaffId();

    if (!staffId) {
        console.error("Staff ID not found. Cannot send notifications.");
        return;
    }

    lowStockProducts.forEach(product => {
        sendNotification(product.name, product.stock);
    });
}


function toggleNotifications() {
    const dialog = document.getElementById("notification-dialog");

    if (!dialog) {
        console.error("Notification dialog not found!");
        return;
    }

    dialog.style.display = dialog.style.display === "none" || dialog.style.display === "" ? "block" : "none";

    updateNotificationUI(); // Refresh notification UI when opened
}

// Ensure script runs after DOM is ready
document.addEventListener("DOMContentLoaded", function () {
    console.log("JavaScript Loaded! ✅");
});

window.history.pushState(null, "", window.location.href);
window.onpopstate = function () {
  window.history.pushState(null, "", window.location.href);
};
