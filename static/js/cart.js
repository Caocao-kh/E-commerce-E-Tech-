/**
 * E-Tech LocalStorage Cart System
 */

const CART_KEY = 'cart';

function getCart() {
    try {
        const cart = localStorage.getItem(CART_KEY);
        return cart ? JSON.parse(cart) : [];
    } catch (e) {
        console.error('Error reading cart from localStorage', e);
        return [];
    }
}

function saveCart(cart) {
    try {
        localStorage.setItem(CART_KEY, JSON.stringify(cart));
        updateCartCount();
    } catch (e) {
        console.error('Error saving cart to localStorage', e);
    }
}

function addToCart(product, quantity = 1) {
    let cart = getCart();
    const existingIndex = cart.findIndex(item => item.id === product.id);

    if (existingIndex > -1) {
        cart[existingIndex].quantity += quantity;
    } else {
        cart.push({
            id: product.id,
            title: product.title || product.name || 'Product',
            price: parseFloat(product.price) || 0,
            oldPrice: parseFloat(product.oldPrice) || 0,
            image: product.image || '',
            category: product.category || '',
            quantity: quantity,
            stock: product.stock || 99
        });
    }

    saveCart(cart);
    if (window.showToast) {
        window.showToast(`Added "${product.title || product.name || 'Product'}" to cart`, 'success');
    }
}

function removeFromCart(productId) {
    let cart = getCart();
    const item = cart.find(i => i.id === productId);
    cart = cart.filter(i => i.id !== productId);
    saveCart(cart);
    if (window.showToast && item) {
        window.showToast(`Removed "${item.title}" from cart`, 'warning');
    }
    renderCartPage();
}

function updateCartQuantity(productId, quantity) {
    let cart = getCart();
    const item = cart.find(i => i.id === productId);
    if (item) {
        if (quantity <= 0) {
            removeFromCart(productId);
            return;
        }
        item.quantity = quantity;
        saveCart(cart);
        renderCartPage();
    }
}

function clearCart() {
    localStorage.removeItem(CART_KEY);
    updateCartCount();
    if (window.showToast) {
        window.showToast('Cart cleared', 'warning');
    }
    renderCartPage();
}

function updateCartCount() {
    const cart = getCart();
    const totalCount = cart.reduce((sum, item) => sum + item.quantity, 0);
    const countElems = document.querySelectorAll('.cart-count');
    countElems.forEach(elem => {
        elem.textContent = totalCount;
    });
}

function renderCartPage() {
    const cartContainer = document.getElementById('cart-items-container');
    const summaryContainer = document.getElementById('cart-summary-container');
    if (!cartContainer) return;

    const cart = getCart();

    if (cart.length === 0) {
        cartContainer.innerHTML = `
            <div class="empty-cart text-center py-5">
                <div class="empty-icon mb-3">
                    <i class="bi bi-cart-x display-1 text-muted"></i>
                </div>
                <h3>Your cart is empty</h3>
                <p class="text-muted">Looks like you haven't added anything to your cart yet.</p>
                <a href="/products" class="btn btn-dark rounded-pill px-4 mt-2">
                    <i class="bi bi-arrow-left me-2"></i> Start Shopping
                </a>
            </div>
        `;
        if (summaryContainer) {
            summaryContainer.innerHTML = `
                <div class="card border-0 shadow-sm rounded-4 p-4">
                    <h5 class="fw-bold mb-3">Order Summary</h5>
                    <p class="text-muted">Add items to view breakdown</p>
                </div>
            `;
        }
        return;
    }

    let subtotal = 0;
    let savings = 0;

    let itemsHtml = `
        <div class="table-responsive">
            <table class="table align-middle text-nowrap">
                <thead>
                    <tr class="text-muted small">
                        <th>PRODUCT</th>
                        <th>PRICE</th>
                        <th class="text-center">QUANTITY</th>
                        <th class="text-end">TOTAL</th>
                        <th class="text-end">ACTION</th>
                    </tr>
                </thead>
                <tbody>
    `;

    cart.forEach(item => {
        const itemTotal = item.price * item.quantity;
        subtotal += itemTotal;
        if (item.oldPrice > item.price) {
            savings += (item.oldPrice - item.price) * item.quantity;
        }

        const imageHtml = item.image ? 
            `<img src="${item.image}" alt="${item.title}" class="rounded-3 me-3" style="width: 64px; height: 64px; object-fit: cover;">` :
            `<div class="bg-light rounded-3 me-3 d-flex align-items-center justify-content-center" style="width: 64px; height: 64px;"><i class="bi bi-box text-muted fs-4"></i></div>`;

        itemsHtml += `
            <tr>
                <td>
                    <div class="d-flex align-items-center">
                        ${imageHtml}
                        <div>
                            <h6 class="mb-0 text-truncate" style="max-width: 200px;">
                                <a href="/product/${item.id}" class="text-dark text-decoration-none fw-semibold">${item.title}</a>
                            </h6>
                            <small class="text-muted text-uppercase">${item.category || ''}</small>
                        </div>
                    </div>
                </td>
                <td>
                    <span class="fw-bold">$${item.price.toFixed(2)}</span>
                    ${item.oldPrice > item.price ? `<br><small class="text-muted text-decoration-line-through">$${item.oldPrice.toFixed(2)}</small>` : ''}
                </td>
                <td class="text-center">
                    <div class="input-group input-group-sm mx-auto" style="width: 110px;">
                        <button class="btn btn-outline-secondary" onclick="updateCartQuantity(${item.id}, ${item.quantity - 1})">-</button>
                        <input type="text" class="form-control text-center bg-white" value="${item.quantity}" readonly>
                        <button class="btn btn-outline-secondary" onclick="updateCartQuantity(${item.id}, ${item.quantity + 1})">+</button>
                    </div>
                </td>
                <td class="text-end fw-bold text-dark">
                    $${itemTotal.toFixed(2)}
                </td>
                <td class="text-end">
                    <button class="btn btn-link text-danger p-0" onclick="removeFromCart(${item.id})" title="Remove">
                        <i class="bi bi-trash fs-5"></i>
                    </button>
                </td>
            </tr>
        `;
    });

    itemsHtml += `
                </tbody>
            </table>
        </div>
        <div class="d-flex justify-content-between align-items-center mt-3">
            <a href="/products" class="btn btn-outline-dark rounded-pill px-4">
                <i class="bi bi-arrow-left me-2"></i> Continue Shopping
            </a>
            <button class="btn btn-outline-danger rounded-pill px-4" onclick="clearCart()">
                <i class="bi bi-trash me-2"></i> Clear Cart
            </button>
        </div>
    `;

    cartContainer.innerHTML = itemsHtml;

    const shipping = subtotal > 100 ? 0 : 15.00;
    const finalTotal = subtotal + shipping;

    if (summaryContainer) {
        summaryContainer.innerHTML = `
            <div class="card border-0 shadow-sm rounded-4 p-4">
                <h5 class="fw-bold mb-4">Order Summary</h5>
                
                <div class="d-flex justify-content-between mb-2">
                    <span class="text-muted">Subtotal</span>
                    <span class="fw-bold">$${subtotal.toFixed(2)}</span>
                </div>
                
                ${savings > 0 ? `
                <div class="d-flex justify-content-between mb-2 text-success">
                    <span>Discount / Savings</span>
                    <span>-$${savings.toFixed(2)}</span>
                </div>` : ''}

                <div class="d-flex justify-content-between mb-3">
                    <span class="text-muted">Estimated Shipping</span>
                    <span>${shipping === 0 ? '<span class="text-success fw-bold">FREE</span>' : '$' + shipping.toFixed(2)}</span>
                </div>

                <div class="mb-3">
                    <div class="input-group">
                        <input type="text" class="form-control" placeholder="Promo Code (Optional)">
                        <button class="btn btn-dark" type="button" onclick="showToast('Promo code applied!', 'success')">Apply</button>
                    </div>
                </div>

                <hr class="my-3">

                <div class="d-flex justify-content-between mb-4 fs-5 fw-bold">
                    <span>Total</span>
                    <span class="text-dark">$${finalTotal.toFixed(2)}</span>
                </div>

                <button class="btn btn-dark btn-lg w-100 rounded-pill shadow-sm" data-bs-toggle="modal" data-bs-target="#checkoutModal">
                    Proceed to Checkout <i class="bi bi-arrow-right ms-2"></i>
                </button>
                <small class="text-muted text-center d-block mt-3">
                    <i class="bi bi-shield-check me-1 text-success"></i> Secure Client Checkout Demo
                </small>
            </div>
        `;
    }
}

// Make globally accessible
window.getCart = getCart;
window.saveCart = saveCart;
window.addToCart = addToCart;
window.removeFromCart = removeFromCart;
window.updateCartQuantity = updateCartQuantity;
window.clearCart = clearCart;
window.updateCartCount = updateCartCount;
window.renderCartPage = renderCartPage;
