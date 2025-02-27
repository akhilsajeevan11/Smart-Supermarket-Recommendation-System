document.addEventListener("DOMContentLoaded", function () {
    updateProductList();
    checkLowStock();
});

let products = [];
let tasks = [];

function addOrUpdateProduct() {
    let name = document.getElementById("product-name").value.trim();
    let category = document.getElementById("category").value;
    let stock = parseInt(document.getElementById("stock-amount").value);
    let promotion = document.getElementById("promotion").value.trim();
    let price = parseFloat(document.getElementById("price").value);
    let imageInput = document.getElementById("product-image");
    let imagePreview = document.getElementById("image-preview");

    if (name === "" || isNaN(stock) || stock <= 0 || isNaN(price) || price <= 0) {
        alert("Please enter valid product details.");
        return;
    }

    // Convert image to Base64 to persist it
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

    if (existingProductIndex !== -1) {
        // Update existing product
        products[existingProductIndex] = { name, category, stock, promotion, price, image };
    } else {
        // Add new product
        products.push({ name, category, stock, promotion, price, image });
    }

    resetForm();
    updateProductList();
    checkLowStock();
}

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

    let rows = products.map((product, index) => `
        <tr>
            <td><img src="${product.image || '#'}" alt="Product Image" width="50" class="img-thumbnail"></td>
            <td>${product.name}</td>
            <td>${product.category}</td>
            <td>${product.stock}</td>
            <td>${product.promotion || "-"}</td>
            <td>$${product.price.toFixed(2)}</td>
            <td>
                <button class='btn btn-danger btn-sm' onclick='deleteProduct(${index})'>Delete</button>
            </td>
        </tr>
    `);

    tableBody.innerHTML = rows.join(""); // More efficient DOM manipulation
}

function deleteProduct(index) {
    products.splice(index, 1);
    updateProductList();
    checkLowStock();
}

function checkLowStock() {
    let lowStockProducts = products.filter(product => product.stock < 5);
    let alertBox = document.getElementById("low-stock-alert");

    if (lowStockProducts.length > 0) {
        alertBox.classList.remove("d-none");
        alertBox.innerText = "Low stock on: " + lowStockProducts.map(p => `${p.name} (${p.stock})`).join(", ");
        tasks = lowStockProducts.map(p => `Restock ${p.name} (${p.stock} left)`);
    } else {
        alertBox.classList.add("d-none");
        tasks = [];
    }

    updateTaskList();
}

function updateTaskList() {
    let taskList = document.getElementById("task-list");
    taskList.innerHTML = "";

    if (tasks.length === 0) {
        taskList.innerHTML = '<li class="list-group-item">No pending tasks</li>';
    } else {
        taskList.innerHTML = tasks.map(task => `<li class="list-group-item">${task}</li>`).join("");
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
