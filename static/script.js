document.addEventListener("DOMContentLoaded", function () {
    const toggleSwitch = document.getElementById("theme-toggle");
    const body = document.body;
    const sunIcon = "☀️";
    const moonIcon = "🌙";

    // Load user preference from localStorage
    if (localStorage.getItem("theme") === "dark") {
        body.classList.add("dark-mode");
        toggleSwitch.innerHTML = sunIcon;
    } else {
        toggleSwitch.innerHTML = moonIcon;
    }

    // Toggle dark mode
    toggleSwitch.addEventListener("click", function () {
        body.classList.toggle("dark-mode");

        if (body.classList.contains("dark-mode")) {
            localStorage.setItem("theme", "dark");
            toggleSwitch.innerHTML = sunIcon;
        } else {
            localStorage.setItem("theme", "light");
            toggleSwitch.innerHTML = moonIcon;
        }
    });
});


document.addEventListener("DOMContentLoaded", function () {
    const uploadForm = document.getElementById("upload-form");
    const fileInput = document.getElementById("file-input");
    const progressBar = document.getElementById("progress-bar");
    const progressContainer = document.getElementById("progress-container");
    const loadingSpinner = document.getElementById("loading-spinner");

    // Drag & Drop
    const dropArea = document.getElementById("drop-area");
    dropArea.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropArea.classList.add("dragging");
    });

    dropArea.addEventListener("dragleave", () => dropArea.classList.remove("dragging"));

    dropArea.addEventListener("drop", (e) => {
        e.preventDefault();
        dropArea.classList.remove("dragging");
        fileInput.files = e.dataTransfer.files;
    });

    // Show progress bar on submit
    uploadForm.addEventListener("submit", function () {
        progressContainer.style.display = "block";
        loadingSpinner.style.display = "block";
        let width = 0;
        let interval = setInterval(() => {
            if (width >= 100) {
                clearInterval(interval);
            } else {
                width += 5;
                progressBar.style.width = width + "%";
            }
        }, 100);
    });
});


