// Initialize SocketIO
const socket = io();

document.addEventListener("DOMContentLoaded", function () {
    updateProductList();
    checkLowStock();
});

let products = [];

function addOrUpdateProduct() {
    let name = document.getElementById("product-name").value.trim();
    let category = document.getElementById("category").value;
    let stock = parseInt(document.getElementById("stock-amount").value);
    let promotion = document.getElementById("promotion").value.trim();
    let price = parseFloat(document.getElementById("price").value);
    let imageInput = document.getElementById("product-image");

    if (name === "" || isNaN(stock) || stock <= 0 || isNaN(price) || price <= 0) {
        alert("Please enter valid product details.");
        return;
    }

    if (imageInput.files.length > 0) {
        let file = imageInput.files[0];
        let reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = function () {
            saveProduct(name, category, stock, promotion, price, reader.result);
        };
    } else {
        let existingProduct = products.find(product => product.name === name);
        saveProduct(name, category, stock, promotion, price, existingProduct ? existingProduct.image : "");
    }
}

function saveProduct(name, category, stock, promotion, price, image) {
    let existingProductIndex = products.findIndex(product => product.name === name);

    const productData = {
        name,
        category,
        stock,
        promotion,
        price,
        image,
        staff_id: getStaffId(),
        product_id: existingProductIndex !== -1 ? products[existingProductIndex].product_id : Date.now().toString()
    };

    if (existingProductIndex !== -1) {
        products[existingProductIndex] = productData;
    } else {
        products.push(productData);
    }

    // Emit the new product to the server
    socket.emit('add_product', productData);

    resetForm();
    updateProductList();
    checkLowStock();
}

function getStaffId() {
    // Retrieve staff_id from the global window object
    const staffId = window.staffId;
    if (!staffId) {
        console.error("Staff ID not found. Please ensure the staff_id is set in the session.");
    }
    return staffId;
}

// Listen for new products from the server
socket.on('new_product', function(product) {
    // Check if product already exists
    const existingProductIndex = products.findIndex(p => p.name === product.name);
    
    if (existingProductIndex !== -1) {
        products[existingProductIndex] = product;
    } else {
        products.push(product);
    }
    
    updateProductList();
    checkLowStock();
});

function resetForm() {
    document.getElementById("product-name").value = "";
    document.getElementById("stock-amount").value = "";
    document.getElementById("promotion").value = "";
    document.getElementById("price").value = "";
    document.getElementById("product-image").value = "";
    document.getElementById("image-preview").src = "#";
    document.getElementById("image-preview").classList.add("d-none");
}

function updateProductList() {
    let tableBody = document.getElementById("product-list");
    tableBody.innerHTML = "";

    if (products.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="7" class="text-center text-muted">No products added</td></tr>`;
        return;
    }

    tableBody.innerHTML = products.map((product) => 
        `<tr>
            <td><img src="${product.image || '#'}" alt="Product Image" width="50" class="img-thumbnail"></td>
            <td>${product.name}</td>
            <td>${product.category}</td>
            <td>${product.stock}</td>
            <td>${product.promotion || "-"}</td>
            <td>$${product.price.toFixed(2)}</td>
            <td>
                <button class='btn btn-danger btn-sm' onclick='deleteProduct("${product.product_id}")'>Delete</button>
            </td>
        </tr>`
    ).join("");
}

function deleteProduct(product_id) {
    const staff_id = getStaffId();
    
    console.log("Attempting to delete product:", product_id); // Debugging
    console.log("Staff ID:", staff_id); // Debugging
    
    if (!product_id || !staff_id) {
        console.error("Product ID and Staff ID are required");
        return;
    }

    // Ensure product_id is passed as a string (if needed)
    socket.emit('delete_product', {
        product_id: String(product_id), // Convert to string if necessary
        staff_id: staff_id
    });
}

// Listen for product deletions
socket.on('product_deleted', function(data) {
    console.log("Product deleted:", data.product_id); // Debugging
    console.log("Type of deleted product_id:", typeof data.product_id); // Debugging
    console.log("Current products before deletion:", products); // Debugging

    // Ensure product_id types match (convert to string if necessary)
    products = products.filter(product => String(product.product_id) !== String(data.product_id));

    console.log("Current products after deletion:", products); // Debugging
    updateProductList();
    checkLowStock();
});

function checkLowStock() {
    let lowStockProducts = products.filter(product => product.stock < 5);
    let alertBox = document.getElementById("low-stock-alert");

    if (lowStockProducts.length > 0) {
        alertBox.classList.remove("d-none");
        alertBox.innerText = "Low stock on: " + lowStockProducts.map(p => `${p.name} (${p.stock})`).join(", ");
    } else {
        alertBox.classList.add("d-none");
    }
}

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

function toggleNotifications() {
    let dialog = document.getElementById('notification-dialog');
    dialog.style.display = dialog.style.display === 'none' || dialog.style.display === '' ? 'block' : 'none';
}
