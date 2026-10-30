/**
 * E-Tech LocalStorage Cart System
 */

const CART_KEY = 'cart';

/**
 * Check if current user is logged in
 * @returns {boolean}
 */
function isUserAuthenticated() {
    if (typeof window.IS_USER_AUTHENTICATED !== 'undefined') {
        return Boolean(window.IS_USER_AUTHENTICATED);
    }
    const authElem = document.getElementById('cart-auth-data');
    if (authElem) {
        return authElem.getAttribute('data-authenticated') === 'true';
    }
    return false;
}

/**
 * Retrieve cart items from localStorage
 * @returns {Array} List of cart item objects
 */
function getCart() {
    try {
        const cart = localStorage.getItem(CART_KEY);
        return cart ? JSON.parse(cart) : [];
    } catch (e) {
        console.error('Error reading cart from localStorage', e);
        return [];
    }
}

/**
 * Save cart items to localStorage and refresh badge counts
 * @param {Array} cart 
 */
function saveCart(cart) {
    try {
        localStorage.setItem(CART_KEY, JSON.stringify(cart));
        updateCartCount();
    } catch (e) {
        console.error('Error saving cart to localStorage', e);
    }
}

/**
 * Add a product to the cart or increase its quantity if already exists
 * @param {Object} product 
 * @param {number} quantity 
 */
function addToCart(product, quantity = 1) {
    let cart = getCart();
    const qtyToAdd = Math.max(1, parseInt(quantity, 10) || 1);
    const existingIndex = cart.findIndex(item => parseInt(item.id, 10) === parseInt(product.id, 10));
    const maxStock = parseInt(product.stock, 10) || 99;

    if (existingIndex > -1) {
        const currentQty = parseInt(cart[existingIndex].quantity, 10) || 1;
        const newQty = currentQty + qtyToAdd;

        if (newQty > maxStock) {
            cart[existingIndex].quantity = maxStock;
            saveCart(cart);
            if (window.showToast) {
                window.showToast(`Updated to maximum available stock (${maxStock} units)`, 'warning');
            }
        } else {
            cart[existingIndex].quantity = newQty;
            saveCart(cart);
            if (window.showToast) {
                window.showToast(`Increased "${product.title || product.name || 'Product'}" quantity to ${cart[existingIndex].quantity}`, 'success');
            }
        }
    } else {
        const initialQty = Math.min(qtyToAdd, maxStock);
        cart.push({
            id: parseInt(product.id, 10),
            title: product.title || product.name || 'Product',
            price: parseFloat(product.price) || 0,
            oldPrice: parseFloat(product.oldPrice) || 0,
            image: product.image || '',
            category: product.category || '',
            quantity: initialQty,
            stock: maxStock
        });
        saveCart(cart);
        if (window.showToast) {
            window.showToast(`Added "${product.title || product.name || 'Product'}" to cart`, 'success');
        }
    }

    renderCartPage();
}

/**
 * Increase quantity of a specific item by 1
 * @param {number|string} productId 
 */
function increaseQuantity(productId) {
    const id = parseInt(productId, 10);
    let cart = getCart();
    const item = cart.find(i => parseInt(i.id, 10) === id);
    if (!item) return;

    const maxStock = parseInt(item.stock, 10) || 99;
    const currentQty = parseInt(item.quantity, 10) || 1;

    if (currentQty >= maxStock) {
        if (window.showToast) {
            window.showToast(`Cannot increase further. Maximum stock limit reached (${maxStock} units)`, 'warning');
        }
        return;
    }

    item.quantity = currentQty + 1;
    saveCart(cart);
    renderCartPage();
    if (window.showToast) {
        window.showToast(`Increased quantity of "${item.title}" to ${item.quantity}`, 'success');
    }
}

/**
 * Decrease quantity of a specific item by 1, or remove it if quantity reaches 0
 * @param {number|string} productId 
 */
function decreaseQuantity(productId) {
    const id = parseInt(productId, 10);
    let cart = getCart();
    const item = cart.find(i => parseInt(i.id, 10) === id);
    if (!item) return;

    const currentQty = parseInt(item.quantity, 10) || 1;

    if (currentQty > 1) {
        item.quantity = currentQty - 1;
        saveCart(cart);
        renderCartPage();
        if (window.showToast) {
            window.showToast(`Decreased quantity of "${item.title}" to ${item.quantity}`, 'info');
        }
    } else {
        removeFromCart(id);
    }
}

/**
 * Update quantity of a specific cart item directly
 * @param {number|string} productId 
 * @param {number|string} quantity 
 */
function updateCartQuantity(productId, quantity) {
    const id = parseInt(productId, 10);
    let cart = getCart();
    const item = cart.find(i => parseInt(i.id, 10) === id);
    if (!item) return;

    const qty = parseInt(quantity, 10);

    if (isNaN(qty) || qty <= 0) {
        removeFromCart(id);
        return;
    }

    const maxStock = parseInt(item.stock, 10) || 99;
    if (qty > maxStock) {
        item.quantity = maxStock;
        if (window.showToast) {
            window.showToast(`Quantity set to maximum available stock (${maxStock})`, 'warning');
        }
    } else {
        item.quantity = qty;
        if (window.showToast) {
            window.showToast(`Updated "${item.title}" quantity to ${item.quantity}`, 'info');
        }
    }

    saveCart(cart);
    renderCartPage();
}

/**
 * Remove a specific item from cart
 * @param {number|string} productId 
 * @param {boolean} notify 
 */
function removeFromCart(productId, notify = true) {
    const id = parseInt(productId, 10);
    let cart = getCart();
    const item = cart.find(i => parseInt(i.id, 10) === id);
    cart = cart.filter(i => parseInt(i.id, 10) !== id);
    saveCart(cart);

    if (notify && window.showToast && item) {
        window.showToast(`Removed "${item.title}" from cart`, 'warning');
    }

    renderCartPage();
}

/**
 * Clear all items from the cart
 * @param {boolean} notify 
 */
function clearCart(notify = true) {
    localStorage.removeItem(CART_KEY);
    updateCartCount();

    if (notify && window.showToast) {
        window.showToast('Your shopping cart has been cleared', 'warning');
    }

    renderCartPage();
}

/**
 * Update cart count badge in navbar and mobile header
 */
function updateCartCount() {
    const cart = getCart();
    const totalCount = cart.reduce((sum, item) => sum + (parseInt(item.quantity, 10) || 0), 0);
    const countElems = document.querySelectorAll('.cart-count');
    countElems.forEach(elem => {
        elem.textContent = totalCount;
    });
}

/**
 * Calculate totals and breakdown of the cart
 */
function getCartSummary() {
    const cart = getCart();
    let subtotal = 0;
    let savings = 0;
    let totalItems = 0;

    cart.forEach(item => {
        const qty = parseInt(item.quantity, 10) || 1;
        const price = parseFloat(item.price) || 0;
        const oldPrice = parseFloat(item.oldPrice) || 0;

        subtotal += price * qty;
        totalItems += qty;

        if (oldPrice > price) {
            savings += (oldPrice - price) * qty;
        }
    });

    const freeShippingThreshold = 100.00;
    const shipping = subtotal === 0 ? 0 : (subtotal >= freeShippingThreshold ? 0 : 15.00);
    const total = subtotal + shipping;

    return {
        subtotal,
        savings,
        shipping,
        freeShippingThreshold,
        total,
        totalItems
    };
}

/**
 * Render the cart page items and order summary
 */
function renderCartPage() {
    const cartContainer = document.getElementById('cart-items-container');
    const summaryContainer = document.getElementById('cart-summary-container');
    if (!cartContainer) return;

    const cart = getCart();

    // Empty Cart State
    if (cart.length === 0) {
        cartContainer.innerHTML = `
            <div class="empty-cart text-center py-5 border rounded-4 bg-white shadow-sm">
                <div class="empty-icon mb-3">
                    <i class="bi bi-cart-x display-1 text-muted"></i>
                </div>
                <h3 class="fw-bold mb-2">Your Shopping Cart is Empty</h3>
                <p class="text-muted mb-4">Looks like you haven't added any products to your cart yet.</p>
                <a href="/products" class="btn btn-dark rounded-pill px-4 py-2">
                    <i class="bi bi-arrow-left me-2"></i> Start Shopping
                </a>
            </div>
        `;
        if (summaryContainer) {
            summaryContainer.innerHTML = `
                <div class="card border-0 shadow-sm rounded-4 p-4 bg-white">
                    <h5 class="fw-bold mb-3">Order Summary</h5>
                    <p class="text-muted small mb-0">Add items to your cart to view order summary and checkout options.</p>
                </div>
            `;
        }
        return;
    }

    const summary = getCartSummary();

    // Cart Items Table
    let itemsHtml = `
        <div class="card border-0 shadow-sm rounded-4 overflow-hidden bg-white mb-4">
            <div class="table-responsive">
                <table class="table align-middle text-nowrap mb-0 cart-table">
                    <thead class="table-light">
                        <tr class="text-muted small text-uppercase">
                            <th class="ps-4 py-3">Product</th>
                            <th class="py-3">Price</th>
                            <th class="text-center py-3">Quantity</th>
                            <th class="text-end py-3">Total</th>
                            <th class="text-end pe-4 py-3">Action</th>
                        </tr>
                    </thead>
                    <tbody>
    `;

    cart.forEach(item => {
        const itemQty = parseInt(item.quantity, 10) || 1;
        const itemPrice = parseFloat(item.price) || 0;
        const itemOldPrice = parseFloat(item.oldPrice) || 0;
        const itemTotal = (itemPrice * itemQty);
        const imageHtml = item.image ? 
            `<img src="${item.image}" alt="${item.title}" class="rounded-3 me-3 border" style="width: 64px; height: 64px; object-fit: cover;">` :
            `<div class="bg-light rounded-3 me-3 d-flex align-items-center justify-content-center border" style="width: 64px; height: 64px;"><i class="bi bi-box text-muted fs-4"></i></div>`;

        itemsHtml += `
            <tr class="cart-item-row" data-id="${item.id}">
                <td class="ps-4 py-3">
                    <div class="d-flex align-items-center">
                        ${imageHtml}
                        <div>
                            <h6 class="mb-0 text-truncate" style="max-width: 220px;">
                                <a href="/product/${item.id}" class="text-dark text-decoration-none fw-semibold">${item.title}</a>
                            </h6>
                            <span class="badge bg-secondary-subtle text-secondary small text-uppercase mt-1">${item.category || 'Product'}</span>
                        </div>
                    </div>
                </td>
                <td class="py-3">
                    <span class="fw-bold text-dark">$${itemPrice.toFixed(2)}</span>
                    ${itemOldPrice > itemPrice ? `<br><small class="text-muted text-decoration-line-through">$${itemOldPrice.toFixed(2)}</small>` : ''}
                </td>
                <td class="text-center py-3">
                    <div class="input-group input-group-sm mx-auto quantity-selector" style="width: 120px;">
                        <button class="btn btn-outline-secondary px-2 btn-cart-dec" type="button" data-cart-action="decrease" data-id="${item.id}" title="Decrease quantity">
                            <i class="bi bi-dash"></i>
                        </button>
                        <input 
                            type="number" 
                            min="1" 
                            max="${item.stock || 99}" 
                            class="form-control text-center bg-white fw-bold px-1 cart-qty-input" 
                            data-cart-action="qty-input"
                            data-id="${item.id}"
                            value="${itemQty}" 
                            title="Direct quantity edit"
                        >
                        <button class="btn btn-outline-secondary px-2 btn-cart-inc" type="button" data-cart-action="increase" data-id="${item.id}" title="Increase quantity">
                            <i class="bi bi-plus"></i>
                        </button>
                    </div>
                </td>
                <td class="text-end fw-bold text-dark py-3">
                    $${itemTotal.toFixed(2)}
                </td>
                <td class="text-end pe-4 py-3">
                    <button class="btn btn-sm btn-outline-danger border-0 rounded-circle p-2 btn-cart-remove" type="button" data-cart-action="remove" data-id="${item.id}" title="Remove item">
                        <i class="bi bi-trash fs-6"></i>
                    </button>
                </td>
            </tr>
        `;
    });

    itemsHtml += `
                    </tbody>
                </table>
            </div>
        </div>

        <div class="d-flex flex-column flex-sm-row justify-content-between align-items-center gap-3">
            <a href="/products" class="btn btn-outline-dark rounded-pill px-4 py-2">
                <i class="bi bi-arrow-left me-2"></i> Continue Shopping
            </a>
            <button class="btn btn-outline-danger rounded-pill px-4 py-2" type="button" data-bs-toggle="modal" data-bs-target="#clearCartModal">
                <i class="bi bi-trash3 me-2"></i> Clear Cart
            </button>
        </div>
    `;

    cartContainer.innerHTML = itemsHtml;

    // Order Summary Calculation & Free Shipping Banner
    if (summaryContainer) {
        const remainingForFreeShipping = Math.max(0, summary.freeShippingThreshold - summary.subtotal);
        const freeShippingPercent = Math.min(100, Math.round((summary.subtotal / summary.freeShippingThreshold) * 100));

        let shippingNoticeHtml = '';
        if (remainingForFreeShipping > 0) {
            shippingNoticeHtml = `
                <div class="mb-3 p-3 bg-light rounded-3 border">
                    <div class="d-flex justify-content-between small mb-1">
                        <span class="text-muted">Free Shipping Progress</span>
                        <span class="fw-bold">${freeShippingPercent}%</span>
                    </div>
                    <div class="progress mb-2" style="height: 6px;">
                        <div class="progress-bar bg-dark" role="progressbar" style="width: ${freeShippingPercent}%" aria-valuenow="${freeShippingPercent}" aria-valuemin="0" aria-valuemax="100"></div>
                    </div>
                    <small class="text-muted d-block">
                        Add <strong class="text-dark">$${remainingForFreeShipping.toFixed(2)}</strong> more to qualify for <strong>FREE Shipping</strong>!
                    </small>
                </div>
            `;
        } else {
            shippingNoticeHtml = `
                <div class="alert alert-success border-0 rounded-3 py-2 px-3 small mb-3 d-flex align-items-center">
                    <i class="bi bi-check-circle-fill me-2 fs-5"></i>
                    <span>You've unlocked <strong>FREE Shipping</strong> on this order!</span>
                </div>
            `;
        }

        summaryContainer.innerHTML = `
            <div class="card border-0 shadow-sm rounded-4 p-4 bg-white cart-summary-card">
                <h5 class="fw-bold mb-3">Order Summary</h5>
                
                ${shippingNoticeHtml}

                <div class="d-flex justify-content-between mb-2">
                    <span class="text-muted">Subtotal (${summary.totalItems} ${summary.totalItems === 1 ? 'item' : 'items'})</span>
                    <span class="fw-bold">$${summary.subtotal.toFixed(2)}</span>
                </div>
                
                ${summary.savings > 0 ? `
                <div class="d-flex justify-content-between mb-2 text-success">
                    <span>Discount / Savings</span>
                    <span class="fw-bold">-$${summary.savings.toFixed(2)}</span>
                </div>` : ''}

                <div class="d-flex justify-content-between mb-3">
                    <span class="text-muted">Estimated Shipping</span>
                    <span>${summary.shipping === 0 ? '<span class="badge bg-success-subtle text-success fw-bold">FREE</span>' : '$' + summary.shipping.toFixed(2)}</span>
                </div>

                <div class="mb-3">
                    <div class="input-group input-group-sm">
                        <input type="text" class="form-control" placeholder="Promo Code (Optional)">
                        <button class="btn btn-dark" type="button" onclick="showToast('Promo code applied!', 'success')">Apply</button>
                    </div>
                </div>

                <hr class="my-3">

                <div class="d-flex justify-content-between mb-4 fs-5 fw-bold">
                    <span>Total</span>
                    <span class="text-dark">$${summary.total.toFixed(2)}</span>
                </div>

                ${isUserAuthenticated() ? `
                    <button class="btn btn-dark btn-lg w-100 rounded-pill shadow-sm" type="button" data-bs-toggle="modal" data-bs-target="#checkoutModal">
                        Proceed to Checkout <i class="bi bi-arrow-right ms-2"></i>
                    </button>
                ` : `
                    <button class="btn btn-dark btn-lg w-100 rounded-pill shadow-sm" type="button" data-bs-toggle="modal" data-bs-target="#loginRequiredModal">
                        <i class="bi bi-lock-fill me-2"></i> Log In to Checkout
                    </button>
                    <div class="text-center mt-2">
                        <small class="text-muted">
                            Please <a href="/login?next=/cart" class="text-dark fw-semibold text-decoration-none">sign in</a> to complete checkout
                        </small>
                    </div>
                `}
                <small class="text-muted text-center d-block mt-3">
                    <i class="bi bi-shield-check me-1 text-success"></i> Secure Client Checkout Demo
                </small>
            </div>
        `;
    }
}

// -------------------------------------------------------------
// Global Delegated Event Listeners for Dynamic Cart Actions
// -------------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
    // Sync cart badge on page load
    updateCartCount();

    // Render if cart container is present
    if (document.getElementById('cart-items-container')) {
        renderCartPage();
    }
});

// Click Delegations for Increase, Decrease, Remove, Clear
document.addEventListener('click', (e) => {
    // Increase quantity
    const incBtn = e.target.closest('.btn-cart-inc, [data-cart-action="increase"]');
    if (incBtn) {
        e.preventDefault();
        const id = parseInt(incBtn.dataset.id || incBtn.getAttribute('data-id'), 10);
        if (id) increaseQuantity(id);
        return;
    }

    // Decrease quantity
    const decBtn = e.target.closest('.btn-cart-dec, [data-cart-action="decrease"]');
    if (decBtn) {
        e.preventDefault();
        const id = parseInt(decBtn.dataset.id || decBtn.getAttribute('data-id'), 10);
        if (id) decreaseQuantity(id);
        return;
    }

    // Remove item
    const removeBtn = e.target.closest('.btn-cart-remove, [data-cart-action="remove"]');
    if (removeBtn) {
        e.preventDefault();
        const id = parseInt(removeBtn.dataset.id || removeBtn.getAttribute('data-id'), 10);
        if (id) removeFromCart(id);
        return;
    }

    // Clear cart confirm button in modal
    const clearBtn = e.target.closest('.btn-cart-clear-confirm, [data-cart-action="clear-all"]');
    if (clearBtn) {
        e.preventDefault();
        clearCart();
        return;
    }
});

// Input Change Delegation for direct quantity editing
document.addEventListener('change', (e) => {
    const qtyInput = e.target.closest('.cart-qty-input, [data-cart-action="qty-input"]');
    if (qtyInput) {
        const id = parseInt(qtyInput.dataset.id || qtyInput.getAttribute('data-id'), 10);
        if (id) {
            updateCartQuantity(id, qtyInput.value);
        }
    }
});

// Global Exports
window.getCart = getCart;
window.saveCart = saveCart;
window.addToCart = addToCart;
window.removeFromCart = removeFromCart;
window.removeItem = removeFromCart;
window.updateCartQuantity = updateCartQuantity;
window.increaseQuantity = increaseQuantity;
window.increaseCartQuantity = increaseQuantity;
window.decreaseQuantity = decreaseQuantity;
window.decreaseCartQuantity = decreaseQuantity;
window.clearCart = clearCart;
window.updateCartCount = updateCartCount;
window.isUserAuthenticated = isUserAuthenticated;
window.getCartSummary = getCartSummary;
window.renderCartPage = renderCartPage;


