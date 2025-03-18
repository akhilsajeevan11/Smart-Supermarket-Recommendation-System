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
      const productName = productItem.querySelector("h3").innerText;
      const productPrice = parseFloat(
        productItem.querySelector(".price").innerText.replace("₹", "")
      );
      const productQty = parseInt(
        productItem.querySelector("input[name='quantity']").value
      );

      const cartItem = {
        name: productName,
        price: productPrice,
        quantity: productQty,
      };

      let cart = JSON.parse(localStorage.getItem("cart")) || [];
      let existingItem = cart.find((item) => item.name === cartItem.name);

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

document.getElementById('check-out').addEventListener('click', function() {
  window.location.href = '/checkout';  // This will trigger the Flask logout route
});

