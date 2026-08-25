/**
 * E-Tech Admin Dashboard JavaScript
 */

document.addEventListener("DOMContentLoaded", () => {
    // ---------------------------------------------
    // Sidebar Toggle for Mobile & Compact Mode
    // ---------------------------------------------
    const sidebarToggle = document.getElementById("sidebar-toggle");
    const adminWrapper = document.getElementById("admin-wrapper");

    if (sidebarToggle && adminWrapper) {
        sidebarToggle.addEventListener("click", () => {
            adminWrapper.classList.toggle("sidebar-collapsed");
        });
    }

    // ---------------------------------------------
    // Sales Canvas Chart (Vanilla HTML5 Canvas)
    // ---------------------------------------------
    const salesCanvas = document.getElementById("salesChart");
    if (salesCanvas && salesCanvas.getContext) {
        renderSalesChart(salesCanvas);
    }

    const ordersCanvas = document.getElementById("ordersChart");
    if (ordersCanvas && ordersCanvas.getContext) {
        renderOrdersChart(ordersCanvas);
    }

    // ---------------------------------------------
    // Admin Table Row Delete Simulation
    // ---------------------------------------------
    let rowToDelete = null;
    const deleteModal = document.getElementById('deleteConfirmModal');
    if (deleteModal) {
        deleteModal.addEventListener('show.bs.modal', (event) => {
            const button = event.relatedTarget;
            rowToDelete = button ? button.closest('tr') : null;
        });

        const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
        if (confirmDeleteBtn) {
            confirmDeleteBtn.addEventListener('click', () => {
                if (rowToDelete) {
                    rowToDelete.classList.add('fade-out');
                    setTimeout(() => rowToDelete.remove(), 300);
                }
                const modalInstance = bootstrap.Modal.getInstance(deleteModal);
                if (modalInstance) modalInstance.hide();
                if (window.showToast) {
                    window.showToast('Item deleted successfully', 'warning');
                }
            });
        }
    }
});

function renderSalesChart(canvas) {
    const ctx = canvas.getContext("2d");
    const width = canvas.width = canvas.parentElement.clientWidth || 500;
    const height = canvas.height = 240;

    const data = [1200, 1900, 3000, 2500, 4200, 3800, 5100, 4800, 6200, 7500, 6900, 8400];
    const labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

    const padding = 40;
    const chartWidth = width - padding * 2;
    const chartHeight = height - padding * 2;
    const maxVal = Math.max(...data) * 1.1;

    ctx.clearRect(0, 0, width, height);

    // Draw Grid Lines
    ctx.strokeStyle = "#e2e8f0";
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
        const y = padding + (chartHeight / 4) * i;
        ctx.beginPath();
        ctx.moveTo(padding, y);
        ctx.lineTo(width - padding, y);
        ctx.stroke();

        ctx.fillStyle = "#94a3b8";
        ctx.font = "11px Inter, sans-serif";
        const val = Math.round(maxVal - (maxVal / 4) * i);
        ctx.fillText("$" + val, 5, y + 4);
    }

    // Draw Gradient Line
    const gradient = ctx.createLinearGradient(0, padding, 0, height - padding);
    gradient.addColorStop(0, "rgba(79, 70, 229, 0.3)");
    gradient.addColorStop(1, "rgba(79, 70, 229, 0.0)");

    ctx.beginPath();
    data.forEach((val, index) => {
        const x = padding + (chartWidth / (data.length - 1)) * index;
        const y = padding + chartHeight - (val / maxVal) * chartHeight;
        if (index === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    });

    // Fill Area
    ctx.lineTo(width - padding, height - padding);
    ctx.lineTo(padding, height - padding);
    ctx.closePath();
    ctx.fillStyle = gradient;
    ctx.fill();

    // Draw Stroke
    ctx.beginPath();
    data.forEach((val, index) => {
        const x = padding + (chartWidth / (data.length - 1)) * index;
        const y = padding + chartHeight - (val / maxVal) * chartHeight;
        if (index === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    });
    ctx.strokeStyle = "#4f46e5";
    ctx.lineWidth = 3;
    ctx.stroke();

    // Draw Points & Labels
    data.forEach((val, index) => {
        const x = padding + (chartWidth / (data.length - 1)) * index;
        const y = padding + chartHeight - (val / maxVal) * chartHeight;

        ctx.beginPath();
        ctx.arc(x, y, 4, 0, Math.PI * 2);
        ctx.fillStyle = "#ffffff";
        ctx.fill();
        ctx.strokeStyle = "#4f46e5";
        ctx.lineWidth = 2;
        ctx.stroke();

        ctx.fillStyle = "#64748b";
        ctx.font = "11px Inter, sans-serif";
        ctx.fillText(labels[index], x - 10, height - 10);
    });
}

function renderOrdersChart(canvas) {
    const ctx = canvas.getContext("2d");
    const width = canvas.width = canvas.parentElement.clientWidth || 500;
    const height = canvas.height = 240;

    const data = [45, 60, 85, 70, 95, 110, 130, 125, 140, 165, 150, 180];
    const labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

    const padding = 40;
    const chartWidth = width - padding * 2;
    const chartHeight = height - padding * 2;
    const maxVal = Math.max(...data) * 1.1;

    ctx.clearRect(0, 0, width, height);

    const barWidth = (chartWidth / data.length) * 0.6;
    const spacing = (chartWidth / data.length);

    data.forEach((val, index) => {
        const x = padding + spacing * index + spacing * 0.2;
        const barH = (val / maxVal) * chartHeight;
        const y = padding + chartHeight - barH;

        ctx.fillStyle = "#0ea5e9";
        ctx.beginPath();
        ctx.roundRect(x, y, barWidth, barH, [4, 4, 0, 0]);
        ctx.fill();

        ctx.fillStyle = "#64748b";
        ctx.font = "11px Inter, sans-serif";
        ctx.fillText(labels[index], x + barWidth / 2 - 10, height - 10);
    });
}
