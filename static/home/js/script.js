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

  var initSwiper = function () {
    var swiper = new Swiper(".main-swiper", {
      speed: 500,
      pagination: {
        el: ".swiper-pagination",
        clickable: true,
      },
    });

    var category_swiper = new Swiper(".category-carousel", {
      slidesPerView: 6,
      spaceBetween: 30,
      speed: 500,
      navigation: {
        nextEl: ".category-carousel-next",
        prevEl: ".category-carousel-prev",
      },
      breakpoints: {
        0: {
          slidesPerView: 2,
        },
        768: {
          slidesPerView: 3,
        },
        991: {
          slidesPerView: 4,
        },
        1500: {
          slidesPerView: 6,
        },
      },
    });

    var brand_swiper = new Swiper(".brand-carousel", {
      slidesPerView: 4,
      spaceBetween: 30,
      speed: 500,
      navigation: {
        nextEl: ".brand-carousel-next",
        prevEl: ".brand-carousel-prev",
      },
      breakpoints: {
        0: {
          slidesPerView: 2,
        },
        768: {
          slidesPerView: 2,
        },
        991: {
          slidesPerView: 3,
        },
        1500: {
          slidesPerView: 4,
        },
      },
    });

    var products_swiper = new Swiper(".products-carousel", {
      slidesPerView: 5,
      spaceBetween: 30,
      speed: 500,
      navigation: {
        nextEl: ".products-carousel-next",
        prevEl: ".products-carousel-prev",
      },
      breakpoints: {
        0: {
          slidesPerView: 1,
        },
        768: {
          slidesPerView: 3,
        },
        991: {
          slidesPerView: 4,
        },
        1500: {
          slidesPerView: 6,
        },
      },
    });
  };

  var initProductQty = function () {
    $(".product-qty").each(function () {
      var $el_product = $(this);
      var quantity = 0;

      $el_product.find(".quantity-right-plus").click(function (e) {
        e.preventDefault();
        var quantity = parseInt($el_product.find("#quantity").val());
        $el_product.find("#quantity").val(quantity + 1);
      });

      $el_product.find(".quantity-left-minus").click(function (e) {
        e.preventDefault();
        var quantity = parseInt($el_product.find("#quantity").val());
        if (quantity > 0) {
          $el_product.find("#quantity").val(quantity - 1);
        }
      });
    });
  };

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
  updateCartUI(); // Ensure cart is updated when the page loads
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
          <span class="text-body-secondary">₹${item.price * item.quantity}</span>
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


// Function to get wishlist from local storage
function getWishlist() {
  return JSON.parse(localStorage.getItem('wishlist')) || [];
}

// Function to add an item to the wishlist dynamically
function addToWishlist(event, btn) {
  event.preventDefault();
  
  let product = btn.closest('.product-item'); // Find the parent product container
  let title = product.querySelector('h3').innerText;
  let qty = product.querySelector('.qty').innerText;
  let price = product.querySelector('.price').innerText.replace('₹', '').trim();
  let image = product.querySelector('img').src;

  let wishlist = getWishlist();

  // Check if item already exists
  if (!wishlist.some(item => item.title === title)) {
      wishlist.push({ title, qty, price, image });
      localStorage.setItem('wishlist', JSON.stringify(wishlist));
      alert('Item added to wishlist!');
  } else {
      alert('Item already in wishlist!');
  }
}

// Function to remove an item from the wishlist
function removeFromWishlist(title) {
  let wishlist = getWishlist();
  wishlist = wishlist.filter(item => item.title !== title);
  localStorage.setItem('wishlist', JSON.stringify(wishlist));
  displayWishlist(); // Refresh the wishlist display
}

// Function to display wishlist on wishlist page
function displayWishlist() {
  let wishlist = getWishlist();
  let wishlistContainer = document.getElementById('wishlist-container');
  
  if (!wishlistContainer) return;

  wishlistContainer.innerHTML = wishlist.length ? '' : '<p>Your wishlist is empty.</p>';
  
  wishlist.forEach(item => {
      wishlistContainer.innerHTML += `
          <div class="card">
              <img src="${item.image}" class="card-img-top" alt="${item.title}">
              <div class="card-body">
                  <h5 class="card-title">${item.title}</h5>
                  <p class="card-text">${item.qty}</p>
                  <p class="card-text">Price: ₹${item.price}</p>
                  <button class="btn btn-danger" onclick="removeFromWishlist('${item.title}')">Remove</button>
              </div>
          </div>
      `;
  });
}

// Load wishlist when page loads
document.addEventListener('DOMContentLoaded', displayWishlist);
