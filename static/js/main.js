/**
 * E-Tech Customer Interface JavaScript Entry Point
 */

document.addEventListener("DOMContentLoaded", () => {
    console.log("E-Tech interface initialized.");

    // Initialize LocalStorage Counts
    if (window.updateCartCount) window.updateCartCount();
    if (window.updateWishlistCount) window.updateWishlistCount();

    // ---------------------------------------------
    // Wishlist Button Handlers across Product Cards
    // ---------------------------------------------
    const wishlistButtons = document.querySelectorAll(".wishlist, [data-wishlist-id]");
    wishlistButtons.forEach((button) => {
        const productId = parseInt(button.getAttribute("data-wishlist-id") || button.dataset.id);
        
        // Sync initial heart icon state
        if (productId && window.isInWishlist && window.isInWishlist(productId)) {
            button.classList.add("active");
            const icon = button.querySelector("i");
            if (icon) {
                icon.classList.remove("bi-heart");
                icon.classList.add("bi-heart-fill");
            }
        }

        button.addEventListener("click", (e) => {
            e.preventDefault();
            e.stopPropagation();
            if (!productId) return;

            const productData = {
                id: productId,
                title: button.getAttribute("data-title") || "Product",
                price: parseFloat(button.getAttribute("data-price")) || 0,
                oldPrice: parseFloat(button.getAttribute("data-old-price")) || 0,
                image: button.getAttribute("data-image") || "",
                category: button.getAttribute("data-category") || ""
            };

            if (window.toggleWishlist) {
                window.toggleWishlist(productData, button);
            }
        });
    });

    // ---------------------------------------------
    // Add to Cart Button Handlers
    // ---------------------------------------------
    const cartButtons = document.querySelectorAll(".add-cart, [data-cart-id]");
    cartButtons.forEach((button) => {
        button.addEventListener("click", (e) => {
            e.preventDefault();
            const productId = parseInt(button.getAttribute("data-cart-id") || button.dataset.id);
            if (!productId) return;

            const qtyInput = document.getElementById("product-qty-input");
            const quantity = qtyInput ? parseInt(qtyInput.value) || 1 : 1;

            const productData = {
                id: productId,
                title: button.getAttribute("data-title") || "Product",
                price: parseFloat(button.getAttribute("data-price")) || 0,
                oldPrice: parseFloat(button.getAttribute("data-old-price")) || 0,
                image: button.getAttribute("data-image") || "",
                category: button.getAttribute("data-category") || ""
            };

            if (window.addToCart) {
                window.addToCart(productData, quantity);
            }

            const icon = button.querySelector("i");
            if (icon) {
                const originalClass = icon.className;
                icon.className = "bi bi-check-lg";
                setTimeout(() => {
                    icon.className = originalClass;
                }, 1200);
            }
        });
    });

    // ---------------------------------------------
    // Product Detail Page Thumbnail Switcher
    // ---------------------------------------------
    const mainDetailImage = document.getElementById("main-detail-image");
    const thumbnails = document.querySelectorAll(".thumbnail-img");

    if (mainDetailImage && thumbnails.length > 0) {
        thumbnails.forEach((thumb) => {
            thumb.addEventListener("click", () => {
                thumbnails.forEach(t => t.classList.remove("border-primary", "active-thumb"));
                thumb.classList.add("border-primary", "active-thumb");
                mainDetailImage.src = thumb.src;
            });
        });
    }

    // ---------------------------------------------
    // Deals Countdown Timer Simulation
    // ---------------------------------------------
    const timerElem = document.getElementById("deal-timer");
    if (timerElem) {
        startCountdown(timerElem, 86400 * 2 + 3600 * 5); // 2 days 5 hours countdown
    }

    // ---------------------------------------------
    // Render Cart or Wishlist if on respective page
    // ---------------------------------------------
    if (document.getElementById("cart-items-container") && window.renderCartPage) {
        window.renderCartPage();
    }

    if (document.getElementById("wishlist-items-container") && window.renderWishlistPage) {
        window.renderWishlistPage();
    }
});

function startCountdown(element, durationSeconds) {
    let timer = durationSeconds;
    setInterval(() => {
        const days = Math.floor(timer / (3600 * 24));
        const hours = Math.floor((timer % (3600 * 24)) / 3600);
        const minutes = Math.floor((timer % 3600) / 60);
        const seconds = Math.floor(timer % 60);

        const daysElem = element.querySelector(".days");
        const hoursElem = element.querySelector(".hours");
        const minutesElem = element.querySelector(".minutes");
        const secondsElem = element.querySelector(".seconds");

        if (daysElem) daysElem.textContent = days.toString().padStart(2, '0');
        if (hoursElem) hoursElem.textContent = hours.toString().padStart(2, '0');
        if (minutesElem) minutesElem.textContent = minutes.toString().padStart(2, '0');
        if (secondsElem) secondsElem.textContent = seconds.toString().padStart(2, '0');

        if (--timer < 0) {
            timer = durationSeconds;
        }
    }, 1000);
}