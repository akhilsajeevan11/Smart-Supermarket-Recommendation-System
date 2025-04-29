document.addEventListener("DOMContentLoaded", function () {
    console.log("✅ DOM Loaded - Fetching sales data...");
    fetchSalesData();

    // Attach form submission event
    const userForm = document.getElementById('userForm');
    if (userForm) {
        userForm.addEventListener('submit', function (e) {
            e.preventDefault();
            createUser();
        });
    }
});

// Fetch Sales Data
function fetchSalesData() {
    console.log("🔄 Fetching sales data...");
    fetch('/sales_data')
        .then(response => response.json())
        .then(data => {
            console.log("✅ Sales Data Received:", data);

            if (data.success) {
                const labels = data.sales_data.map(item => item.product_name);
                const salesValues = data.sales_data.map(item => item.total_sales);
                renderSalesChart(labels, salesValues);
            } else {
                console.error("❌ Error fetching sales data:", data.error);
            }
        })
        .catch(error => console.error("❌ Fetch Error:", error));
}

// Render Chart
function renderSalesChart(labels, salesValues) {
    console.log("🎨 Rendering Sales Chart...");

    const canvas = document.getElementById("salesChart");
    if (!canvas) {
        console.error("❌ Canvas element 'salesChart' not found!");
        return;
    }

    const ctx = canvas.getContext("2d");

    // Destroy existing chart if it exists
    if (window.salesChart && typeof window.salesChart.destroy === "function") {
        console.log("🗑️ Destroying previous chart...");
        window.salesChart.destroy();
    }

    // Create new chart instance
    window.salesChart = new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                label: "Total Sales",
                data: salesValues,
                backgroundColor: "rgba(54, 162, 235, 0.6)"
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: { y: { beginAtZero: true } }
        }
    });

    console.log("✅ Chart Rendered Successfully!");
}

// Show Section Function (Sidebar Navigation)
function showSection(sectionId) {
    document.querySelectorAll('.content > div').forEach(div => div.style.display = 'none');
    document.getElementById(sectionId).style.display = 'block';

    // Re-fetch data when clicking Dashboard
    if (sectionId === 'dashboard') {
        fetchSalesData();
    }

    if (window.innerWidth < 768) {
        toggleSidebar();
    }
}

// Toggle Sidebar for Mobile View
function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('active');
}

// ✅ User Management - Create User Function
async function createUser() {
    console.log("createUser function called");  // Debugging
    const notyf = new Notyf({
        position: {
          x: 'center',  // 👈 center horizontally
          y: 'top',     // 👈 top vertically
        }
      });
      
    const userData = {
        username: document.getElementById("username").value,
        email: document.getElementById("email").value,
        password: document.getElementById("password").value,
        role: document.getElementById("role").value
    };

    console.log("User data:", userData);  // Debugging

    try {
        const response = await fetch('/admin/create_user', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(userData)
        });

        const result = await response.json();
        const messageDiv = document.getElementById("message");

        if (response.ok) {
            messageDiv.innerHTML = `<div class="alert alert-success">${result.message}</div>`;
            // ✅ Clear form values
            document.getElementById("username").value = "";
            document.getElementById("email").value = "";
            document.getElementById("password").value = "";
            document.getElementById("role").value = "Manager";  // Reset to default role
            
            // ✅ Refresh the page after 2 seconds
            setTimeout(() => {
                window.location.reload();
            }, 2000);
        } else {
            messageDiv.innerHTML = `<div class="alert alert-danger">${result.error || 'Failed to create user'}</div>`;
        }
    } catch (error) {
        console.error('Error:', error);
        document.getElementById("message").innerHTML = 
            `<div class="alert alert-danger">An error occurred. Please try again.</div>`;
    }
}

function deleteUser(userId) {
  const notyf = new Notyf({
    position: {
      x: 'center',  // 👈 center horizontally
      y: 'top',     // 👈 top vertically
    }
  });

  if (confirm("Are you sure you want to delete this user?")) {
    fetch(`/admin/delete_user/${userId}`, {
      method: "DELETE",
    })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          notyf.success("User deleted successfully");
          // Refresh the page after 2 seconds
          setTimeout(() => {
            window.location.reload();
          }, 2000);
        } else {
          notyf.error("Error deleting user: " + data.message);
        }
      })
      .catch(error => {
        console.error("Error:", error);
        notyf.error("An error occurred while deleting the user.");
      });
  }
}

window.history.pushState(null, "", window.location.href);
window.onpopstate = function () {
  window.history.pushState(null, "", window.location.href);
};
