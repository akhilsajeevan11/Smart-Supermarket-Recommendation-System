document.addEventListener("DOMContentLoaded", function () {
  initPreloader();
  initSwipers();
  // initWishlist();
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

// ✅ Initialize Swiper Sliders Efficiently
function initSwipers() {
  const categories = ["frozen", "bakery", "dairy-eggs", "beverages", "newly-arrived"];
  categories.forEach(category => {
      new Swiper(`#${category} .products-carousel`, {
          slidesPerView: 1,
          spaceBetween: 10,
          navigation: {
              nextEl: `#${category} .products-carousel-next`,
              prevEl: `#${category} .products-carousel-prev`,
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
  document.querySelectorAll(".wishlist-btn").forEach(button => {
      button.addEventListener("click", addToWishlist);
  });

  document.getElementById("wishlist-popup-close")?.addEventListener("click", closeWishlistPopup);
  displayWishlist(false);
}

function getWishlist() {
  return JSON.parse(localStorage.getItem("wishlist")) || [];
}

function displayWishlist(triggeredByUser = false) {
  let wishlist = getWishlist();
  let wishlistContainer = document.getElementById("wishlist-popup-content");

  if (!wishlistContainer) return;
  wishlistContainer.innerHTML = wishlist.length ? "" : "<p>Your wishlist is empty.</p>";

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
  event.preventDefault();
  let product = event.target.closest(".product-item");
  if (!product) return;

  let title = product.querySelector(".title")?.innerText;
  let price = parseFloat(product.querySelector(".price")?.innerText.replace("₹", "")) || 0;
  let image = product.querySelector("img")?.src;
  let wishlist = getWishlist();

  if (!wishlist.some(item => item.title === title)) {
      wishlist.push({ title, price, image, qty: 1 });
      localStorage.setItem("wishlist", JSON.stringify(wishlist));
      alert("✅ Item added to wishlist!");
  } else {
      alert("⚠️ Item already in wishlist!");
  }
  displayWishlist(false);
}

function removeFromWishlist(title) {
  let wishlist = getWishlist();
  wishlist = wishlist.filter(item => item.title !== title);
  localStorage.setItem("wishlist", JSON.stringify(wishlist));
  displayWishlist(true);
}

function showWishlistPopup() {
  document.getElementById("wishlist-popup").style.display = "block";
}

function closeWishlistPopup() {
  document.getElementById("wishlist-popup").style.display = "none";
}

// ✅ Cart Management
function initCart() {
  document.querySelectorAll(".add-to-cart").forEach(button => {
      button.addEventListener("click", addToCart);
  });

  updateCartUI();
}

async function addToCart(event, btn) {
  event.preventDefault(); // ✅ Prevent page reload

  let product = btn.closest(".product-item"); // ✅ Find the product container
  if (!product) {
      console.error("❌ Could not find product element!");
      return;
  }

  let productId = product.getAttribute("data-product-id"); 
  let name = product.querySelector("h3")?.innerText.trim(); // ✅ Select product name correctly
  let price = parseFloat(product.querySelector(".price")?.innerText.replace("₹", "")) || 0;
  let image = product.querySelector("img")?.getAttribute("src"); // ✅ Use getAttribute("src")
  let quantity = parseInt(product.querySelector(".input-number")?.value) || 1; // ✅ Extract quantity

  if (!productId || !name || isNaN(price) || !image) {
      console.error("❌ Missing product details!", { productId, name, price, image });
      return;
  }

  let cart = JSON.parse(localStorage.getItem("cart")) || [];
  let existingItem = cart.find(item => item.product_id === productId);

  if (existingItem) {
      existingItem.quantity += quantity;
  } else {
      cart.push({ product_id: productId, name, price, quantity, image });
  }

  localStorage.setItem("cart", JSON.stringify(cart));
  updateCartUI();

  // ✅ Fetch recommended products from the backend
  try {
      let response = await fetch("/similar_products", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ product_name: name }) // Send product name
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
  }
}





function displayRecommendedProducts(products) {
  let recommendationsContainer = document.querySelector("#recommended-products .row");
  recommendationsContainer.innerHTML = ""; // Clear previous content

  if (products.length === 0) {
      recommendationsContainer.innerHTML = "<p class='text-muted text-center'>No recommendations available.</p>";
      return;
  }

  products.forEach(product => {
      let productCard = `
          <div class="col">
              <div class="card shadow-sm border-0 h-100 text-center p-2">
                  <img src="${product.image || '/static/default-product.jpg'}" 
                      class="card-img-top mx-auto" 
                      alt="${product.product_name}" 
                      style="width: 80px; height: 80px; object-fit: cover;">

                  <div class="card-body p-2">
                      <h6 class="card-title text-truncate" style="max-width: 100px;">${product.product_name}</h6>
                      <button class="btn btn-sm btn-primary w-100 mt-2" 
                          onclick="addToCart(event, this)">
                          🛒 Add to Cart
                      </button>
                  </div>
              </div>
          </div>`;
      recommendationsContainer.innerHTML += productCard;
  });
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
                    <small class="text-body-secondary">Qty: ${item.quantity}</small>
                </div>
                <span class="text-body-secondary">₹${(item.price * item.quantity).toFixed(2)}</span>
                <button class="btn btn-sm btn-danger remove-item" data-index="${index}">×</button>
            </li>`;
    });

    cartTotalDisplay.textContent = `₹${total.toFixed(2)}`;
    totalAmount.textContent = `₹${total.toFixed(2)}`;
    cartCount.textContent = count;

    attachRemoveEventListeners();
}


function attachRemoveEventListeners() {
  document.querySelectorAll(".remove-item").forEach(button => {
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
  document.getElementById("checkout-btn")?.addEventListener("click", proceedToCheckout);
}

function proceedToCheckout() {
  let cart = JSON.parse(localStorage.getItem("cart")) || [];

  if (cart.length === 0) {
      alert("⚠️ Your cart is empty. Add items before proceeding to checkout!");
      return;
  }

  fetch('/checkout', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ cart_items: cart })
  })
  .then(response => response.json())
  .then(data => {
      if (data.transaction_id) {
          window.location.href = `/payment?transaction_id=${data.transaction_id}&total_amount=${data.total_amount}`;
      } else {
          alert(data.error || "Checkout failed!");
      }
  })
  .catch(error => console.error("❌ Checkout error:", error));
}

document.addEventListener("DOMContentLoaded", function () {
  updateCartUI();
});
