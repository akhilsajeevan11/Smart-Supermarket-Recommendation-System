(function ($) {
  "use strict";

  var initPreloader = function () {
    $(document).ready(function ($) {
      var Body = $("body");
      Body.addClass("preloader-site");
    });
    $(window).load(function () {
      $(".preloader-wrapper").fadeOut();
      $("body").removeClass("preloader-site");
    });
  };

  // init Chocolat light box
  var initChocolat = function () {
    Chocolat(document.querySelectorAll(".image-link"), {
      imageSize: "contain",
      loop: true,
    });
  };


  document.addEventListener("DOMContentLoaded", function () {
    const frozenSwiper = new Swiper("#frozen .products-carousel", {
      slidesPerView: 1, // Default for extra small screens
      spaceBetween: 10, // Default spacing
      navigation: {
        nextEl: "#frozen .products-carousel-next",
        prevEl: "#frozen .products-carousel-prev",
      },
      loop: true, // Enables infinite scrolling
      autoplay: {
        delay: 3000, // Auto-slide every 3 seconds
        disableOnInteraction: false,
      },
      breakpoints: {
        480: { slidesPerView: 2, spaceBetween: 15 }, // Small screens (phones)
        768: { slidesPerView: 3, spaceBetween: 20 }, // Tablets
        1024: { slidesPerView: 4, spaceBetween: 25 }, // Small desktops
        1280: { slidesPerView: 5, spaceBetween: 30 }, // Large screens
      },
    });
  });
  

  document.addEventListener("DOMContentLoaded", function () {
    const frozenSwiper = new Swiper("#bakery .products-carousel", {
      slidesPerView: 1, // Default for extra small screens
      spaceBetween: 10, // Default spacing
      navigation: {
        nextEl: "#bakery .products-carousel-next",
        prevEl: "#bakery .products-carousel-prev",
      },
      loop: true, // Enables infinite scrolling
      autoplay: {
        delay: 3000, // Auto-slide every 3 seconds
        disableOnInteraction: false,
      },
      breakpoints: {
        480: { slidesPerView: 2, spaceBetween: 15 }, // Small screens (phones)
        768: { slidesPerView: 3, spaceBetween: 20 }, // Tablets
        1024: { slidesPerView: 4, spaceBetween: 25 }, // Small desktops
        1280: { slidesPerView: 5, spaceBetween: 30 }, // Large screens
      },
    });
  });

  document.addEventListener("DOMContentLoaded", function () {
    const frozenSwiper = new Swiper("#dairy-eggs .products-carousel", {
      slidesPerView: 1, // Default for extra small screens
      spaceBetween: 10, // Default spacing
      navigation: {
        nextEl: "#dairy-eggs .products-carousel-next",
        prevEl: "#dairy-eggs .products-carousel-prev",
      },
      loop: true, // Enables infinite scrolling
      autoplay: {
        delay: 3000, // Auto-slide every 3 seconds
        disableOnInteraction: false,
      },
      breakpoints: {
        480: { slidesPerView: 2, spaceBetween: 15 }, // Small screens (phones)
        768: { slidesPerView: 3, spaceBetween: 20 }, // Tablets
        1024: { slidesPerView: 4, spaceBetween: 25 }, // Small desktops
        1280: { slidesPerView: 5, spaceBetween: 30 }, // Large screens
      },
    });
  });

  document.addEventListener("DOMContentLoaded", function () {
    const frozenSwiper = new Swiper("#beverages .products-carousel", {
      slidesPerView: 1, // Default for extra small screens
      spaceBetween: 10, // Default spacing
      navigation: {
        nextEl: "#beverages .products-carousel-next",
        prevEl: "#beverages .products-carousel-prev",
      },
      loop: true, // Enables infinite scrolling
      autoplay: {
        delay: 3000, // Auto-slide every 3 seconds
        disableOnInteraction: false,
      },
      breakpoints: {
        480: { slidesPerView: 2, spaceBetween: 15 }, // Small screens (phones)
        768: { slidesPerView: 3, spaceBetween: 20 }, // Tablets
        1024: { slidesPerView: 4, spaceBetween: 25 }, // Small desktops
        1280: { slidesPerView: 5, spaceBetween: 30 }, // Large screens
      },
    });
  });

  document.addEventListener("DOMContentLoaded", function () {
    const frozenSwiper = new Swiper("#newly-arrived .brand-carousel", {
      slidesPerView: 1, // Default for extra small screens
      spaceBetween: 10, // Default spacing
      navigation: {
        nextEl: "#newly-arrived .brand-carousel-next",
        prevEl: "#newly-arrived .brand-carousel-prev",
      },
      loop: true, // Makes sure it scrolls infinitely
      autoplay: {
        delay: 3000, // Auto slide every 3 seconds
        disableOnInteraction: false,
      },
      breakpoints: {
        480: {
          slidesPerView: 2,
          spaceBetween: 15,
        },
        768: {
          slidesPerView: 3,
          spaceBetween: 20,
        },
        1024: {
          slidesPerView: 4,
          spaceBetween: 25,
        },
        1280: {
          slidesPerView: 5,
          spaceBetween: 30,
        },
      },
    });
  });
  

  // init jarallax parallax
  var initJarallax = function () {
    jarallax(document.querySelectorAll(".jarallax"));

    jarallax(document.querySelectorAll(".jarallax-keep-img"), {
      keepImg: true,
    });
  };

  // document ready
  $(document).ready(function () {
    initPreloader();
    initSwiper();
    initProductQty();
    initJarallax();
    initChocolat();
  }); // End of a document
})(jQuery);

//Add to cart Start
document.addEventListener("DOMContentLoaded", function () {
  updateCartUI();
  document.querySelectorAll(".add-to-cart-btn").forEach((button) => {
    button.addEventListener("click", function (event) {
      event.preventDefault();

      const productItem = this.closest(".product-item");
      const productId = productItem.getAttribute("data-product-id");
      const productName = productItem.querySelector("h3").innerText;
      const productPrice = parseFloat(
        productItem.querySelector(".price").innerText.replace("₹", "")
      );
      const productQty = parseInt(
        productItem.querySelector("input[name='quantity']").value
      );

      const cartItem = {
        product_id:productId,
        name: productName,
        price: productPrice,
        quantity: productQty,
      };

      let cart = JSON.parse(localStorage.getItem("cart")) || [];
      let existingItem = cart.find((item) => item.product_id === cartItem.product_id);
      if (existingItem) {
        existingItem.quantity += cartItem.quantity;
      } else {
        cart.push(cartItem);
        alert("Item Added To Cart");
      }

      localStorage.setItem("cart", JSON.stringify(cart));
      updateCartUI();
    });
  });

  function updateCartUI() {
    const cartTotalDisplay = document.querySelector(".cart-total");
    const cartList = document.querySelector(".cart-items");
    const cartTotal = document.querySelector(".total-amount");
    const cartCount = document.querySelector(".cart-count");

    if (!cartTotalDisplay || !cartTotal || !cartList || !cartCount) {
      console.error("Cart elements missing in the DOM!");
      return;
    }

    let cart = JSON.parse(localStorage.getItem("cart")) || [];
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
          <span class="text-body-secondary">₹${
            item.price * item.quantity
          }</span>
          <button class="btn btn-sm btn-danger remove-item" data-index="${index}">×</button>
        </li>
      `;
    });

    // Update total amount in the cart dropdown
    cartTotalDisplay.textContent = `₹${total}`;
    cartTotal.textContent = `₹${total}`;
    cartCount.textContent = count;

    // Attach event listeners to remove buttons
    document.querySelectorAll(".remove-item").forEach((button) => {
      button.addEventListener("click", function () {
        const index = this.getAttribute("data-index");
        cart.splice(index, 1);
        localStorage.setItem("cart", JSON.stringify(cart));
        updateCartUI();
      });
    });
  }
});

// Add to cart End

/// Function to get wishlist from local storage
// Get wishlist from localStorage
function getWishlist() {
  return JSON.parse(localStorage.getItem("wishlist")) || [];
}

// Function to add an item to the wishlist
function addToWishlist(event, btn) {
  event.preventDefault();

  let product = btn.closest(".product-item");
  let title = product.querySelector("h3").innerText;
  let qty = product.querySelector(".qty").innerText;
  let price = product.querySelector(".price").innerText.replace("₹", "").trim();
  let image = product.querySelector("img").src;

  let wishlist = getWishlist();

  if (!wishlist.some((item) => item.title === title)) {
    wishlist.push({ title, qty, price, image });
    localStorage.setItem("wishlist", JSON.stringify(wishlist));
    alert("Item added to wishlist!");
  } else {
    alert("Item already in wishlist!");
  }

  displayWishlist(false);
}

// Function to remove an item from the wishlist
function removeFromWishlist(title) {
  let wishlist = getWishlist();
  wishlist = wishlist.filter((item) => item.title !== title);
  localStorage.setItem("wishlist", JSON.stringify(wishlist));
  displayWishlist(false);
}

// Function to display wishlist in popup
function displayWishlist(triggeredByUser = false) {
  let wishlist = getWishlist();
  let wishlistContainer = document.getElementById("wishlist-popup-content");

  // Clear previous content
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
        <td>
          <button class="remove-btn" onclick="removeFromWishlist('${item.title}')">❌</button>
        </td>
      </tr>
    `;
  });

  if (triggeredByUser) {
    showWishlistPopup();
  }
}

function showWishlistPopup() {
  const wishlistPopup = document.getElementById("wishlist-popup");
  wishlistPopup.style.display = "flex";
  wishlistPopup.style.justifyContent = "center";
  wishlistPopup.style.alignItems = "center";
}

function closeWishlistPopup() {
  document.getElementById("wishlist-popup").style.display = "none";
}

document.getElementById("wishlist-btn").addEventListener("click", function () {
  displayWishlist(true);
});

document.querySelectorAll(".add-to-wishlist-btn").forEach((button) => {
  button.addEventListener("click", function (event) {
    addToWishlist(event, this);
  });
});

window.addEventListener("load", function () {
  closeWishlistPopup();
});

document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll(".dropdown-item").forEach((item) => {
    item.addEventListener("click", function (e) {
      const targetId = this.getAttribute("href").substring(1);
      const targetSection = document.getElementById(targetId);

      if (targetSection) {
        e.preventDefault();
        targetSection.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    });
  });
});





function proceedToCheckout() {
  const cart = JSON.parse(localStorage.getItem('cart')) || [];

  // Calculate total amount
  const totalAmount = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);

  // Prepare data for checkout
  const cartData = cart.map(item => ({
    product_id: item.product_id, // Ensure this matches the product ID in your database
    product_name: item.product_name, // Optional: Include product name for debugging
    quantity: item.quantity,
    amount: item.price * item.quantity // Calculate total amount for each item
  }));

  // Log data for debugging
  console.log("Cart data:", cartData);
  console.log("Total amount:", totalAmount);

  // Send cart data and total amount to the checkout route
  fetch('/checkout', {
    method: 'POST',  // Ensure this is a POST request
    headers: {
      'Content-Type': 'application/json',  // Ensure the correct Content-Type header
    },
    body: JSON.stringify({ cart_items: cartData, total_amount: totalAmount }),  // Ensure the body is JSON
  })
  .then(response => {
    if (response.redirected) {
      window.location.href = response.url; // Redirect to the payment page
    } else {
      return response.json();
    }
  })
  .then(data => {
    if (data && data.error) {
      alert('Checkout failed: ' + data.error);
    }
  })
  .catch(error => {
    console.error('Error:', error);
    alert('Checkout failed. Please try again.');
  });
}



function addToCart(productId) {
  console.log("Product ID:", productId); // Debugging: Log the product ID

  const productItem = document.querySelector(`[data-product-id="${productId}"]`);
  if (!productItem) {
      console.error("Product item not found for ID:", productId);
      return;
  }

  const productName = productItem.querySelector('h3').textContent;
  const productPrice = productItem.querySelector('.price').textContent.replace('₹', '');
  const productQuantity = productItem.querySelector('.input-number').value;

  console.log("Product Name:", productName); // Debugging: Log the product name
  console.log("Product Price:", productPrice); // Debugging: Log the product price
  console.log("Product Quantity:", productQuantity); // Debugging: Log the product quantity

  const cartItem = {
      product_id: parseInt(productId),
      product_name: productName,  // Fix: Corrected property reference
      quantity: parseInt(productQuantity),
      amount: parseFloat(productPrice)
  };

  console.log("Cart Item:", cartItem); // Debugging: Log the cart item

  fetch('/add-to-cart', {
      method: 'POST',
      headers: {
          'Content-Type': 'application/json',
      },
      body: JSON.stringify(cartItem),
  })
  .then(response => response.json())
  .then(data => {
      if (data.success) {
          console.log("Item added to cart:", data.cart); // Debugging: Log the updated cart
          updateCartUI(data.cart);
          calculateCartTotal();
      } else {
          alert('Failed to add item to cart');
      }
  })
  .catch(error => {
      console.error('Error:', error);
  });
}





// profile toogle logout

document.addEventListener("DOMContentLoaded", () => {
  const profileBtn = document.getElementById("profile-btn");
  const logoutContainer = document.getElementById("logout-container");
  const logoutBtn = document.getElementById("logout-btn");

  profileBtn.addEventListener("mouseenter", () => {
    logoutContainer.style.display = "block";
  });

  profileBtn.addEventListener("mouseleave", () => {
    setTimeout(() => {
      if (!logoutContainer.matches(":hover")) {
        logoutContainer.style.display = "none";
      }
    }, 400);
  });

  logoutContainer.addEventListener("mouseleave", () => {
    logoutContainer.style.display = "none";
  });

  logoutBtn.addEventListener("click", () => {
    alert("Logging out..."); // Replace this with your logout function
  });
});


// logout

document.getElementById('logout-btn').addEventListener('click', function() {
  window.location.href = '/logout';  // This will trigger the Flask logout route
});

document.getElementById('check-out').addEventListener('click', async function() {
    try {
        // Get cart items from localStorage
        const cart = JSON.parse(localStorage.getItem('cart')) || [];
        
        // Prepare data for checkout
        const cartData = cart.map(item => ({
            product_id: item.id,
            quantity: item.quantity,
            price: item.price // Ensure price is a number
        }));
        // console.log(item.price, typeof item.price)

        // Send checkout request
        const response = await fetch('/checkout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ cart_items: cartData })
        });

        const data = await response.json();
        
        if (response.ok) {
            // Redirect to payment page with transaction ID
            window.location.href = `/payment?transaction_id=${data.transaction_id}`;
        } else {
            alert('Checkout failed: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Checkout error:', error);
        alert('Checkout failed. Please try again.');
    }
});

document.getElementById('payBtn').onclick = async function () {
    try {
        // Get transaction_id from URL
        const transactionId = new URLSearchParams(window.location.search).get('transaction_id');
        if (!transactionId) {
            throw new Error('Transaction ID not found');
        }

        // Create order with transaction_id
        const res = await fetch('/create_order', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ transaction_id: transactionId })
        });

        const order = await res.json();

        if (!res.ok) {
            throw new Error(order.error || 'Failed to create order');
        }

        // Open Razorpay payment window
        const options = {
            "key": "rzp_test_3UulXQvQM07Hh2", // Your Razorpay key
            "amount": order.amount,
            "currency": order.currency,
            "order_id": order.id,
            "handler": function (response) {
                fetch('/payment_verification', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        ...response,
                        transaction_id: transactionId
                    })
                }).then(res => res.json())
                  .then(data => {
                    if (data.status === 'success') {
                        window.location.href = '/order_success';
                    } else {
                        alert('Payment verification failed');
                    }
                  });
            }
        };

        const rzp1 = new Razorpay(options);
        rzp1.open();
    } catch (error) {
        console.error('Payment error:', error);
        alert('Payment failed: ' + error.message);
    }
};

function updateCartTotal(totalAmount) {
    // Select the total amount element
    const totalAmountElement = document.querySelector('.total-amount');
    
    // Update the total amount displayed
    totalAmountElement.textContent = `₹${totalAmount}`;
}

// Example usage:
// When an item is added to the cart, calculate the total and update the UI
function addToCart(productId, price) {
    // Add the product to the cart (logic here)
    
    // Calculate the new total
    const newTotal = calculateCartTotal(); // Assume this function calculates the total
    
    // Update the UI
    updateCartTotal(newTotal);
}

function initSwiper() {
    const swiper = new Swiper('.swiper', {
        // Swiper configuration options
        loop: true,
        pagination: {
            el: '.swiper-pagination',
        },
        navigation: {
            nextEl: '.swiper-button-next',
            prevEl: '.swiper-button-prev',
        },
    });
}

function calculateCartTotal() {
    const cart = JSON.parse(localStorage.getItem('cart')) || [];
    const totalAmount = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    document.querySelector('.total-amount').textContent = `₹${totalAmount.toFixed(2)}`;
}

function initProductQty() {
    document.querySelectorAll('.product-qty').forEach(qty => {
        const input = qty.querySelector('.input-number');
        const minusBtn = qty.querySelector('.quantity-left-minus');
        const plusBtn = qty.querySelector('.quantity-right-plus');

        minusBtn.addEventListener('click', () => {
            let value = parseInt(input.value);
            if (value > 1) {
                input.value = value - 1;
            }
        });

        plusBtn.addEventListener('click', () => {
            let value = parseInt(input.value);
            input.value = value + 1;
        });
    });
}

document.addEventListener("DOMContentLoaded", function () {
    const element = document.getElementById('your-element-id');
    if (element) {
        // Your code here
    } else {
        console.error("Element not found: #your-element-id");
    }
});



