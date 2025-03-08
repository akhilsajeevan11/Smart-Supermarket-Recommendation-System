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

    if (existingProductIndex !== -1) {
        products[existingProductIndex] = { name, category, stock, promotion, price, image };
    } else {
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

    tableBody.innerHTML = products.map((product, index) => `
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
    `).join("");
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
