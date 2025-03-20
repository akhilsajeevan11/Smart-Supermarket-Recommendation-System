// Notify Staff
function notifyStaff() {
    const lowStockProducts = document.querySelectorAll('#low-stock-products tr');
    const managerId = window.managerId; // Get manager_id from the global variable

    lowStockProducts.forEach(row => {
        const productId = row.getAttribute('data-product-id'); // Get product_id from the data attribute
        const productName = row.cells[0].textContent;
        const stockQuantity = row.cells[1].textContent;

        // Send data to backend
        fetch('/notify_staff', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                product_id: productId, // Include product_id
                product_name: productName,
                stock_quantity: stockQuantity,
            }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log('Notification inserted:', data.message);
            } else {
                console.error('Error:', data.message);
            }
        })
        .catch(error => console.error('Error:', error));
    });

    // Show success message
    document.getElementById('notification-response').innerHTML = `
        <div class="alert alert-success">Notification sent to staff!</div>
    `;
}

// Load Sections
function loadSection(section) {
    let content = document.getElementById('section-content');
    let stockSection = document.getElementById('stock-section');

    if (section === 'stock') {
        content.style.display = 'none'; // Hide the dashboard
        stockSection.style.display = 'block'; // Show the stock section
    } else {
        content.style.display = 'block'; // Show the dashboard
        stockSection.style.display = 'none'; // Hide the stock section
    }
}

// Load Charts
document.addEventListener('DOMContentLoaded', function() {
    renderChart('salesChart', 'line', ['Jan', 'Feb', 'Mar', 'Apr', 'May'], [12000, 15000, 17000, 20000, 23000], 'Sales Trend', '#4f46e5');
    renderChart('demandChart', 'bar', ['Product A', 'Product B', 'Product C'], [300, 450, 500], 'Future Demand', '#FF5733');
    renderChart('topProductsChart', 'pie', ['Product X', 'Product Y', 'Product Z'], [50, 30, 20], 'High Performing Products', ['#33FF57', '#3357FF', '#FF33A1']);
    renderChart('customerChart', 'doughnut', ['Preference A', 'Preference B', 'Preference C'], [40, 35, 25], 'Customer Preferences', ['#FFD433', '#FF5733', '#33FF57']);
});

// Chart.js Function
function renderChart(canvasId, type, labels, data, label, colors) {
    let ctx = document.getElementById(canvasId).getContext('2d');
    new Chart(ctx, {
        type: type,
        data: {
            labels: labels,
            datasets: [{
                label: label,
                data: data,
                backgroundColor: Array.isArray(colors) ? colors : colors,
                borderWidth: 1,
            }]
        }
    });
}

// Toggle Sidebar for Mobile
function toggleSidebar() {
    let sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('open');
}

socket.on('connect', () => {
    console.log('Connected to Socket.IO server');
});
