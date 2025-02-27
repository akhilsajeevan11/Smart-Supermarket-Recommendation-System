// Toggle Sidebar for Mobile
function toggleSidebar() {
    let sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('open');
}

// Load Sections
function loadSection(section) {
    let content = document.getElementById('section-content');
    if (section === 'stock') {
        content.innerHTML = `
            <h2 class="text-center">Stock Tracking</h2>
            <div id="stock-alert" class="alert alert-info">Stock levels are up to date.</div>
            <button class='btn btn-danger' onclick='notifyStaff()'>Notify Staff</button>`;
    } else {
        location.reload();
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
