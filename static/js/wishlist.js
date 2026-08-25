/**
 * E-Tech LocalStorage Wishlist System
 */

const WISHLIST_KEY = 'wishlist';

function getWishlist() {
    try {
        const wishlist = localStorage.getItem(WISHLIST_KEY);
        return wishlist ? JSON.parse(wishlist) : [];
    } catch (e) {
        console.error('Error reading wishlist from localStorage', e);
        return [];
    }
}

function saveWishlist(wishlist) {
    try {
        localStorage.setItem(WISHLIST_KEY, JSON.stringify(wishlist));
        updateWishlistCount();
    } catch (e) {
        console.error('Error saving wishlist to localStorage', e);
    }
}

function isInWishlist(productId) {
    const wishlist = getWishlist();
    return wishlist.some(item => item.id === productId);
}

function addToWishlist(product) {
    let wishlist = getWishlist();
    if (!isInWishlist(product.id)) {
        wishlist.push({
            id: product.id,
            title: product.title || product.name || 'Product',
            price: parseFloat(product.price) || 0,
            oldPrice: parseFloat(product.oldPrice) || 0,
            image: product.image || '',
            category: product.category || '',
            rating: product.rating || 5,
            stock: product.stock || 10
        });
        saveWishlist(wishlist);
        if (window.showToast) {
            window.showToast(`Added "${product.title || product.name || 'Product'}" to wishlist`, 'success');
        }
    }
}

function removeFromWishlist(productId) {
    let wishlist = getWishlist();
    const item = wishlist.find(i => i.id === productId);
    wishlist = wishlist.filter(i => i.id !== productId);
    saveWishlist(wishlist);
    if (window.showToast && item) {
        window.showToast(`Removed "${item.title}" from wishlist`, 'warning');
    }
    renderWishlistPage();
}

function toggleWishlist(product, buttonElem = null) {
    if (isInWishlist(product.id)) {
        removeFromWishlist(product.id);
        if (buttonElem) {
            buttonElem.classList.remove('active');
            const icon = buttonElem.querySelector('i');
            if (icon) {
                icon.classList.remove('bi-heart-fill');
                icon.classList.add('bi-heart');
            }
        }
    } else {
        addToWishlist(product);
        if (buttonElem) {
            buttonElem.classList.add('active');
            const icon = buttonElem.querySelector('i');
            if (icon) {
                icon.classList.remove('bi-heart');
                icon.classList.add('bi-heart-fill');
            }
        }
    }
}

function updateWishlistCount() {
    const wishlist = getWishlist();
    const countElems = document.querySelectorAll('.wishlist-count');
    countElems.forEach(elem => {
        elem.textContent = wishlist.length;
    });
}

function moveWishlistItemToCart(productId) {
    const wishlist = getWishlist();
    const item = wishlist.find(i => i.id === productId);
    if (item) {
        if (window.addToCart) {
            window.addToCart(item, 1);
        }
        removeFromWishlist(productId);
    }
}

function renderWishlistPage() {
    const wishlistContainer = document.getElementById('wishlist-items-container');
    if (!wishlistContainer) return;

    const wishlist = getWishlist();

    if (wishlist.length === 0) {
        wishlistContainer.innerHTML = `
            <div class="empty-wishlist text-center py-5">
                <div class="empty-icon mb-3">
                    <i class="bi bi-heart display-1 text-muted"></i>
                </div>
                <h3>Your wishlist is empty</h3>
                <p class="text-muted">Save products you love and find them here later.</p>
                <a href="/products" class="btn btn-dark rounded-pill px-4 mt-2">
                    <i class="bi bi-arrow-left me-2"></i> Explore Products
                </a>
            </div>
        `;
        return;
    }

    let html = '<div class="row g-4">';
    wishlist.forEach(product => {
        const imageHtml = product.image ?
            `<img src="${product.image}" class="card-img-top object-fit-cover" alt="${product.title}" style="height: 220px;">` :
            `<div class="bg-light card-img-top d-flex align-items-center justify-content-center text-muted" style="height: 220px;"><i class="bi bi-box fs-1"></i></div>`;

        html += `
            <div class="col-12 col-sm-6 col-md-4 col-lg-3">
                <div class="card h-100 border-0 shadow-sm rounded-4 overflow-hidden position-relative product-card">
                    <button class="btn btn-sm btn-light position-absolute top-0 end-0 m-2 rounded-circle shadow-sm" onclick="removeFromWishlist(${product.id})" title="Remove from wishlist">
                        <i class="bi bi-x-lg"></i>
                    </button>
                    ${imageHtml}
                    <div class="card-body d-flex flex-column">
                        <span class="text-uppercase text-muted small fw-semibold">${product.category || ''}</span>
                        <h6 class="card-title fw-bold text-truncate mb-2">
                            <a href="/product/${product.id}" class="text-dark text-decoration-none">${product.title}</a>
                        </h6>
                        <div class="mt-auto d-flex justify-content-between align-items-center">
                            <div>
                                <span class="fw-bold text-dark fs-5">$${product.price.toFixed(2)}</span>
                                ${product.oldPrice > product.price ? `<small class="text-muted text-decoration-line-through ms-1">$${product.oldPrice.toFixed(2)}</small>` : ''}
                            </div>
                            <button class="btn btn-dark rounded-pill btn-sm px-3" onclick="moveWishlistItemToCart(${product.id})">
                                <i class="bi bi-bag-plus me-1"></i> Add to Cart
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
    html += '</div>';

    wishlistContainer.innerHTML = html;
}

window.getWishlist = getWishlist;
window.saveWishlist = saveWishlist;
window.isInWishlist = isInWishlist;
window.addToWishlist = addToWishlist;
window.removeFromWishlist = removeFromWishlist;
window.toggleWishlist = toggleWishlist;
window.updateWishlistCount = updateWishlistCount;
window.moveWishlistItemToCart = moveWishlistItemToCart;
window.renderWishlistPage = renderWishlistPage;
