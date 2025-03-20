document.addEventListener("DOMContentLoaded", function() {
    // Initialize Chart
    const ctx = document.getElementById("salesChart").getContext("2d");
    new Chart(ctx, {
        type: "bar",
        data: {
            labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
            datasets: [{
                label: "Sales (in $1000s)",
                data: [12, 19, 3, 5, 2, 3],
                backgroundColor: "rgba(54, 162, 235, 0.5)"
            }]
        },
        
    });

    // Handle user form submission
    document.getElementById("content").addEventListener("submit", function(event) {
        if (event.target.id === "userForm") {
            event.preventDefault();
            createUser();
        }
    });
});

function showSection(sectionId) {
    document.querySelectorAll('.content > div').forEach(div => div.style.display = 'none');
    document.getElementById(sectionId).style.display = 'block';
    if (window.innerWidth < 768) {
        toggleSidebar();
    }
}

function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('active');
}



// usermanagment script

async function createUser() {
    const userData = {
        username: document.getElementById("username").value,
        email: document.getElementById("email").value,
        password: document.getElementById("password").value,
        role: document.getElementById("role").value
    };

    try {
        const response = await fetch('/admin/create_user', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(userData)
        });

        const result = await response.json();
        const messageDiv = document.getElementById("message");
        
        if (response.ok) {
            messageDiv.innerHTML = `<div class="alert alert-success">${result.message}</div>`;
            document.getElementById("userForm").reset();
        } else {
            messageDiv.innerHTML = `<div class="alert alert-danger">${result.error}</div>`;
        }
    } catch (error) {
        console.error('Error:', error);
        document.getElementById("message").innerHTML = 
            `<div class="alert alert-danger">An error occurred. Please try again.</div>`;
    }
}
