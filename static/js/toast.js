/**
 * E-Tech Toast Notification System
 */

function showToast(message, type = 'success', duration = 3000) {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        container.style.zIndex = '1090';
        document.body.appendChild(container);
    }

    const toastId = 'toast-' + Date.now();
    const bgClass = type === 'danger' ? 'text-bg-danger' : (type === 'warning' ? 'text-bg-warning' : 'text-bg-dark');
    const icon = type === 'danger' ? 'bi-x-circle' : (type === 'warning' ? 'bi-exclamation-circle' : 'bi-check-circle-fill');

    const toastHtml = `
        <div id="${toastId}" class="toast align-items-center ${bgClass} border-0 show shadow-lg mb-2" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body d-flex align-items-center fs-6">
                    <i class="bi ${icon} me-2 fs-5 text-accent"></i>
                    <span>${message}</span>
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;

    container.insertAdjacentHTML('beforeend', toastHtml);

    const toastElem = document.getElementById(toastId);
    setTimeout(() => {
        if (toastElem) {
            toastElem.classList.remove('show');
            setTimeout(() => toastElem.remove(), 300);
        }
    }, duration);
}

window.showToast = showToast;
