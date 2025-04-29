document.addEventListener("DOMContentLoaded", function () {
  initPreloader();
  initWishlist();
  initSwipers();
  initCart();
  initProductQty();
  initCheckout();
});

// ✅ Preloader Initialization
function initPreloader() {
  $(document).ready(function () {
    $("body").addClass("preloader-site");
  });
  $(window).on("load", function () {
    $(".preloader-wrapper").fadeOut();
    $("body").removeClass("preloader-site");
  });
}

// ✅ Initialize Swiper Sliders Efficientl
function initSwipers() {
  const categories = [
    { id: "frozen", carouselClass: "products-carousel" },
    { id: "bakery", carouselClass: "products-carousel" },
    { id: "dairy-eggs", carouselClass: "products-carousel" },
    { id: "beverages", carouselClass: "products-carousel" },
    { id: "newly-arrived", carouselClass: "brand-carousel" },
  ];

  categories.forEach((category) => {
    new Swiper(`#${category.id} .${category.carouselClass}`, {
      slidesPerView: 1,
      spaceBetween: 10,
      navigation: {
        nextEl: `#${category.id} .${category.carouselClass}-next`,
        prevEl: `#${category.id} .${category.carouselClass}-prev`,
      },
      loop: true,
      autoplay: { delay: 3000, disableOnInteraction: false },
      breakpoints: {
        480: { slidesPerView: 2, spaceBetween: 15 },
        768: { slidesPerView: 3, spaceBetween: 20 },
        1024: { slidesPerView: 4, spaceBetween: 25 },
        1280: { slidesPerView: 5, spaceBetween: 30 },
      },
    });
  });
}

// ✅ Wishlist Management
function initWishlist() {
  document.querySelectorAll(".wishlist-btn").forEach((button) => {
    button.addEventListener("click", addToWishlist);
  });

  document
    .getElementById("wishlist-popup-close")
    ?.addEventListener("click", closeWishlistPopup);

  // Add this line to make the wishlist button open the modal
  document
    .getElementById("wishlist-btn")
    ?.addEventListener("click", () => displayWishlist(true));

  displayWishlist(false);
}

function getWishlist() {
  return JSON.parse(localStorage.getItem("wishlist")) || [];
}

function displayWishlist(triggeredByUser = false) {
  let wishlist = getWishlist();
  let wishlistContainer = document.getElementById("wishlist-popup-content");
  console.log("displayWishlist called. Triggered by user:", triggeredByUser);

  if (!wishlistContainer) return;
  wishlistContainer.innerHTML = wishlist.length
    ? ""
    : "<p>Your wishlist is empty.</p>";

  wishlist.forEach((item) => {
    wishlistContainer.innerHTML += `
          <tr>
              <td><img src="${item.image}" alt="${item.title}" class="wishlist-img"></td>
              <td>${item.title}</td>
              <td>₹${item.price}</td>
              <td>${item.qty}</td>
              <td><button class="remove-btn" onclick="removeFromWishlist('${item.title}')">❌</button></td>
          </tr>`;
  });

  if (triggeredByUser) showWishlistPopup();
}

function addToWishlist(event) {
  const notyf = new Notyf({
    position: {
      x: 'center',  // 👈 center horizontally
      y: 'top',     // 👈 top vertically
    }
  });
  event.preventDefault();
  let product = event.target.closest(".product-item");
  if (!product) return;

  let title = product.querySelector("h3")?.innerText;
  let price =
    parseFloat(product.querySelector(".price")?.innerText.replace("₹", "")) ||
    0;
  let image = product.querySelector("img")?.src;
  let wishlist = getWishlist();

  if (!wishlist.some((item) => item.title === title)) {
    wishlist.push({ title, price, image, qty: 1 });
    localStorage.setItem("wishlist", JSON.stringify(wishlist));
    notyf.success("Item added to wishlist!");
  } else {
    notyf.success("Item already in wishlist!");
  }
  displayWishlist(false);
}

function removeFromWishlist(title) {
  const notyf = new Notyf({
    position: {
      x: 'center',  // 👈 center horizontally
      y: 'top',     // 👈 top vertically
    }
  });
  let wishlist = getWishlist();
  wishlist = wishlist.filter((item) => item.title !== title);
  localStorage.setItem("wishlist", JSON.stringify(wishlist));
  notyf.error("Item removed from wishlist!");
  displayWishlist(true);
}

function showWishlistPopup() {
  document.getElementById("wishlist-popup").style.display = "block";
  document.getElementById("wishlist-popup").classList.add("show");
}

function closeWishlistPopup() {
  document.getElementById("wishlist-popup").style.display = "none";
  document.getElementById("wishlist-popup").classList.remove("show");
}

// ✅ Modified Cart Initialization
function initCart() {
  // Add event delegation for all add-to-cart buttons
  document.body.addEventListener('click', function(event) {
    const addToCartBtn = event.target.closest('.add-to-cart');
    if (addToCartBtn) {
      event.preventDefault();
      handleUniversalAddToCart(addToCartBtn);
    }
  });

  // Keep existing code for recommended products
  document.querySelectorAll(".btn-add-to-cart").forEach((button) => {
    button.addEventListener("click", addRecommendedToCart);
  });

  updateCartUI();
}

// ✅ New Universal Add to Cart Handler
function handleUniversalAddToCart(button) {
  const notyf = new Notyf({
    position: {
      x: 'center',  // 👈 center horizontally
      y: 'top',     // 👈 top vertically
    }
  });
  const productData = {
    productId: button.dataset.productId,
    name: button.dataset.name,
    price: parseFloat(button.dataset.price),
    image: button.dataset.image,
    quantity: 1
  };

  console.log("Product Data:", productData); // Debugging

  if (!productData.productId || !productData.name || isNaN(productData.price)) {
    console.error("❌ Invalid product data:", productData);
    return;
  }

  let cart = JSON.parse(localStorage.getItem("cart")) || [];
  const existingItem = cart.find(item => item.product_id === productData.productId);

  if (existingItem) {
    existingItem.quantity += productData.quantity;
  } else {
    cart.push({
      product_id: productData.productId,
      name: productData.name,
      price: productData.price,
      quantity: productData.quantity,
      image: productData.image
    });
  }

  localStorage.setItem("cart", JSON.stringify(cart));
  notyf.success("Product added to cart");
  updateCartUI();
}

// ✅ Keep existing addToCart function unchanged
async function addToCart(event, btn) {
  event.preventDefault();
  const notyf = new Notyf({
    position: {
      x: 'center',  // 👈 center horizontally
      y: 'top',     // 👈 top vertically
    }
  });
  let product = btn.closest(".product-item");
  if (!product) {
    console.error("❌ Could not find product element!");
    return;
  }

  let productId = product.getAttribute("data-product-id");
  let name = product.querySelector("h3")?.innerText.trim();
  let price = parseFloat(product.querySelector(".price")?.innerText.replace("₹", "")) || 0;
  let image = product.querySelector("img")?.getAttribute("src");
  let quantity = parseInt(product.querySelector(".input-number")?.value) || 1;

  if (!productId || !name || isNaN(price) || !image) {
    console.error("❌ Missing product details!", { productId, name, price, image });
    return;
  }

  let cart = JSON.parse(localStorage.getItem("cart")) || [];
  let existingItem = cart.find((item) => item.product_id === productId);

  if (existingItem) {
    existingItem.quantity += quantity;
  } else {
    cart.push({ product_id: productId, name, price, quantity, image });
  }

  localStorage.setItem("cart", JSON.stringify(cart));
  // alert("✅ Product Added to Cart");
  notyf.success("Product added to cart");
  updateCartUI();

  // ✅ Fetch and Display Recommended Products
  fetchRecommendedProducts(name);
}

// ✅ Fetch Recommended Products
async function fetchRecommendedProducts(productName) {
  let recommendationsContainer = document.querySelector("#recommended-products .row");
  recommendationsContainer.innerHTML = `
    <div class="spinner-container">
      <div class="spinner-border text-primary" role="status"></div>
      <p class="loading-text">Loading recommendations...</p>
    </div>
  `;

  try {
    let response = await fetch("/similar_products", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ product_name: productName }),
    });

    let data = await response.json();
    if (data.success) {
      displayRecommendedProducts(data.similar_products);
    } else {
      console.warn("⚠️ No recommendations found.");
      displayRecommendedProducts([]);
    }
  } catch (error) {
    console.error("❌ Error fetching recommended products:", error);
    displayRecommendedProducts([]);
  }
}

function displayRecommendedProducts(products) {
  let recommendationsContainer = document.querySelector("#recommended-products .row");
  recommendationsContainer.innerHTML = "";

  if (products.length === 0) {
    recommendationsContainer.innerHTML = "<p class='text-muted text-center'>No recommendations available.</p>";
    return;
  }

  products.forEach((product) => {
    let productCard = `
      <div class="recommended-item">
        <div class="Rcard">
          <div class="Rcard-body">
            <h5 class="Rcard-title">${product.product_name}</h5>
            <button class="btn-add-to-cart"
                    data-product-id="${product.product_id}"
                    data-name="${product.product_name}"
                    data-price="${product.price}"
                    data-image="${product.image}">
              Add to Cart
            </button>
          </div>
        </div>
      </div>
    `;
    recommendationsContainer.innerHTML += productCard;
  });

  // ✅ Attach event listeners using existing handler
  document.querySelectorAll("#recommended-products .btn-add-to-cart").forEach((button) => {
    button.addEventListener("click", function(event) {
      event.preventDefault();
      handleUniversalAddToCart(button);
    });
  });
}


// ✅ Add to Cart for Recommended Products
async function addRecommendedToCart(event) {
  event.preventDefault();

  let btn = event.target;
  let product = btn.closest(".recommended-item");

  if (!product) {
    console.error("❌ Could not find recommended product element!");
    return;
  }

  let productId = product.getAttribute("data-product-id");
  let name = product.getAttribute("data-name");
  let price = parseFloat(product.getAttribute("data-price")) || 50;
  let image = product.getAttribute("data-image") || "default.jpg";
  let quantity = 1;

  if (!productId || !name || isNaN(price)) {
    console.error("❌ Missing product details!", { productId, name, price, image });
    return;
  }

  let cart = JSON.parse(localStorage.getItem("cart")) || [];
  let existingItem = cart.find((item) => item.product_id === productId);

  if (existingItem) {
    existingItem.quantity += quantity;
  } else {
    cart.push({ product_id: productId, name, price, quantity, image, is_recommended: true });
  }

  localStorage.setItem("cart", JSON.stringify(cart));
  notyf.success("Recommended Product Added to Cart");
  updateCartUI();
}

function updateCartUI() {
  const cart = JSON.parse(localStorage.getItem("cart")) || [];
  const cartList = document.querySelector(".cart-items");
  const cartTotalDisplay = document.querySelector(".cart-total");
  const totalAmount = document.querySelector(".total-amount");
  const cartCount = document.querySelector(".cart-count");

  if (!cartList || !cartTotalDisplay || !totalAmount || !cartCount) {
    console.error("❌ Cart elements missing in DOM!");
    return;
  }

  let total = 0;
  let count = 0;
  cartList.innerHTML = "";

  cart.forEach((item, index) => {
    total += item.price * item.quantity;
    count += item.quantity;

    cartList.innerHTML += `
            <li class="list-group-item d-flex justify-content-between lh-sm">
                <div>
                    <h6 class="my-0">${item.name}</h6>
                    <small class="text-body-secondary">Qty: ${
                      item.quantity
                    }</small>
                </div>
                <span class="text-body-secondary">₹${(
                  item.price * item.quantity
                ).toFixed(2)}</span>
                <button class="btn btn-sm btn-danger remove-item" data-index="${index}">×</button>
            </li>`;
  });

  cartTotalDisplay.textContent = `₹${total.toFixed(2)}`;
  totalAmount.textContent = `₹${total.toFixed(2)}`;
  cartCount.textContent = count;

  attachRemoveEventListeners();
}

function attachRemoveEventListeners() {
  document.querySelectorAll(".remove-item").forEach((button) => {
    button.addEventListener("click", function () {
      let index = parseInt(this.getAttribute("data-index"));
      removeFromCart(index);
    });
  });
}

function removeFromCart(index) {
  let cart = JSON.parse(localStorage.getItem("cart")) || [];
  if (index >= 0 && index < cart.length) {
    cart.splice(index, 1);
    localStorage.setItem("cart", JSON.stringify(cart));
    updateCartUI();
  }
}

// ✅ Checkout Process
function initCheckout() {
  document
    .getElementById("checkout-btn")
    ?.addEventListener("click", proceedToCheckout);
}

function proceedToCheckout() {
  let cart = JSON.parse(localStorage.getItem("cart")) || [];

  if (cart.length === 0) {
    alert("⚠️ Your cart is empty. Add items before proceeding to checkout!");
    return;
  }

  fetch("/checkout", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ cart_items: cart }),
  })
    .then((response) => response.json())
    .then((data) => {
      if (data.transaction_id) {
        window.location.href = `/payment?transaction_id=${data.transaction_id}&total_amount=${data.total_amount}`;
      } else {
        alert(data.error || "Checkout failed!");
      }
    })
    .catch((error) => console.error("❌ Checkout error:", error));
}

document.addEventListener("DOMContentLoaded", function () {
  updateCartUI();
});

function closeWishlistPopup() {
  let wishlistPopup = document.getElementById("wishlist-popup");
  if (wishlistPopup) {
    wishlistPopup.style.display = "none";
  } else {
    console.error("❌ Wishlist popup element not found!");
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const profileBtn = document.getElementById("profile-btn");
  const logoutContainer = document.getElementById("logout-container");

  profileBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    logoutContainer.style.display =
      logoutContainer.style.display === "block" ? "none" : "block";
  });

  document.addEventListener("click", () => {
    logoutContainer.style.display = "none";
  });

  logoutContainer.addEventListener("click", (e) => {
    e.stopPropagation();
  });
});

function initProductQty() {
  document
    .querySelectorAll(".quantity-left-minus, .quantity-right-plus")
    .forEach((button) => {
      button.addEventListener("click", function () {
        const input =
          this.closest(".input-group").querySelector(".input-number");
        let quantity = parseInt(input.value);

        if (this.classList.contains("quantity-left-minus")) {
          // Decrease quantity (minimum 1)
          quantity = Math.max(1, quantity - 1);
        } else if (this.classList.contains("quantity-right-plus")) {
          // Increase quantity
          quantity += 1;
        }

        input.value = quantity; // Update the input value
      });
    });
}

// Redirect to login page if the user tries to navigate back/forward after logout
window.addEventListener("popstate", function (event) {
  // Check if the user is logged out
  fetch("/check-session")
    .then((response) => response.json())
    .then((data) => {
      if (!data.loggedIn) {
        // Redirect to the login page
        window.location.href = "/";
      }
    });
});
