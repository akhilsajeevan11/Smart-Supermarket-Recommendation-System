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
