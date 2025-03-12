document.addEventListener("DOMContentLoaded", function() {
    // Load dashboard.html by default
    loadPage("/admin/dashboard"); 
   

    // Handle sidebar navigation clicks
    document.querySelectorAll(".nav-link").forEach(link => {
        link.addEventListener("click", function(event) {
            event.preventDefault(); // Prevent default navigation
            const pageUrl = this.getAttribute("href");
            loadPage(pageUrl);
        });
    });

    // Handle user form submission
    document.getElementById("content").addEventListener("submit", function(event) {
        if (event.target.id === "userForm") {
            event.preventDefault();
            createUser();
        }
    });
});

function loadPage(url) {
    fetch(url)
        .then(response => response.text())
        .then(data => {
            const contentDiv = document.getElementById("content");
            contentDiv.innerHTML = data;
            executeScripts(contentDiv);
        })
        .catch(error => console.error("Error loading page:", error));
}

// Function to execute scripts after dynamic fetch
function executeScripts(container) {
    container.querySelectorAll("script").forEach(oldScript => {
        const newScript = document.createElement("script");
        if (oldScript.src) {
            newScript.src = oldScript.src;
            newScript.onload = () => console.log(`Loaded script: ${newScript.src}`);
        } else {
            newScript.textContent = oldScript.textContent;
        }
        document.body.appendChild(newScript);
        oldScript.remove();
    });
}

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
