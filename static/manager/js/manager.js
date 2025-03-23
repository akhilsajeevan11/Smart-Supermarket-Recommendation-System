// Notify Staff
function notifyStaff() {
    const lowStockProducts = document.querySelectorAll('#low-stock-products tr');
    const managerId = window.managerId; // Get manager_id from the global variable
    let notificationMessages = [];

    lowStockProducts.forEach(row => {
        const productId = row.getAttribute('data-product-id'); // Get product_id from the data attribute
        const productName = row.cells[0].textContent;
        const stockQuantity = row.cells[1].textContent;

        fetch('/notify_staff', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                product_id: productId,
                product_name: productName,
                stock_quantity: stockQuantity,
            }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                notificationMessages.push(`✔️ ${productName} - ${data.message}`);
            } else {
                notificationMessages.push(`❌ ${productName} - ${data.message}`);
            }
            updateNotificationResponse(notificationMessages);
        })
        .catch(error => {
            notificationMessages.push(`❌ ${productName} - Error`);
            updateNotificationResponse(notificationMessages);
        });
    });
}

// Display success/failure messages for notifications
function updateNotificationResponse(messages) {
    document.getElementById('notification-response').innerHTML = messages.map(msg => `<div>${msg}</div>`).join('');
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

function fetchSalesAnalytics() {
    // Fetch Sales Data
    fetch('/sales_analytics')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const salesLabels = data.sales_data.map(item => item.product_name);
                const salesValues = data.sales_data.map(item => item.total_sales);
                const revenueValues = data.sales_data.map(item => item.revenue);

                renderChart('salesChart', 'bar', salesLabels, salesValues, 'Total Sales', '#4f46e5');
                renderChart('topProductsChart', 'pie', salesLabels, revenueValues, 'Revenue Distribution', ['#33FF57', '#3357FF', '#FF33A1']);
            } else {
                console.error("Error fetching sales data:", data.error);
            }
        })
        .catch(error => console.error("Fetch error:", error));

    // Fetch Future Demand Products
    fetch('/future_demand')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const demandLabels = data.future_demand.map(item => item.product_name);
                const demandValues = new Array(demandLabels.length).fill(1); // Equal values for visual representation

                renderChart('demandChart', 'bar', demandLabels, demandValues, 'Future Demand', '#FF5733');
            } else {
                console.error("Error fetching future demand:", data.error);
            }
        })
        .catch(error => console.error("Fetch error:", error));

    // Fetch Customer Preferences
    fetch('/customer_preferences')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const preferenceLabels = data.customer_preferences.map(item => item.product_name);
                const preferenceValues = data.customer_preferences.map(item => item.total_quantity);

                renderChart('customerChart', 'doughnut', preferenceLabels, preferenceValues, 'Customer Preferences', ['#FFD433', '#FF5733', '#33FF57']);
            } else {
                console.error("Error fetching customer preferences:", data.error);
            }
        })
        .catch(error => console.error("Fetch error:", error));
}


// Load Charts & Setup Live Updates on Page Load
document.addEventListener('DOMContentLoaded', function() {
    fetchSalesAnalytics(); // Load live sales data
    setupSocketListeners(); // Enable WebSocket updates

    renderChart('demandChart', 'bar', ['Product A', 'Product B', 'Product C'], [300, 450, 500], 'Future Demand', '#FF5733');
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

// WebSocket (Socket.IO) Connection
const socket = io(); // Connect to the WebSocket server

function setupSocketListeners() {
    socket.on('low_stock_alert', (data) => {
        console.log("🔴 Low Stock Alert Received:", data);
        updateLowStockTable(data);
    });
}

// Update Low Stock Table on Alert
function updateLowStockTable(stockData) {
    let tableBody = document.getElementById("low-stock-products");
    tableBody.innerHTML = ''; // Clear old data

    stockData.forEach(item => {
        let row = `<tr data-product-id="${item.product_id}">
                        <td>${item.product_name}</td>
                        <td>${item.stock_quantity}</td>
                   </tr>`;
        tableBody.innerHTML += row;
    });

    // Show alert if new data received
    document.getElementById('notification-response').innerHTML = `
        <div class="alert alert-warning">⚠️ New low-stock alert received!</div>
    `;
}

// Toggle Sidebar for Mobile
function toggleSidebar() {
    let sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('open');
}

// Log WebSocket Connection
socket.on('connect', () => {
    console.log('Connected to Socket.IO server');
});
