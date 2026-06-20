/* -------------------------------------------------------------
 * BrainForge AI - Frontend Interactive Controller
 * AJAX Form Handling, Dynamic Loader Simulation, Task Checklist
 * ------------------------------------------------------------- */

function initializeBrainForge() {
    const form = document.getElementById("idea-submission-form");
    const overlay = document.getElementById("loading-overlay");
    const loadingStep = document.getElementById("loading-step");
    const progressBar = document.getElementById("loading-progress");
    const errorAlert = document.getElementById("form-error-alert");
    const errorAlertText = document.getElementById("error-alert-text");

    // Indicators
    const indClarify = document.getElementById("ind-clarify");
    const indFeasibility = document.getElementById("ind-feasibility");
    const indRisks = document.getElementById("ind-risks");
    const indScenarios = document.getElementById("ind-scenarios");
    const indRoadmap = document.getElementById("ind-roadmap");

    if (form) {
        form.addEventListener("submit", function (e) {
            e.preventDefault();

            // Clear previous errors
            errorAlert.classList.add("hidden");
            document.querySelectorAll(".field-error").forEach(el => el.textContent = "");

            // Read form data
            const formData = new FormData(form);

            // Show loading overlay
            overlay.classList.remove("hidden");
            
            // Progress Bar simulation settings
            let progress = 5;
            let currentPhase = 1;
            progressBar.style.width = progress + "%";

            // Start step messages simulation
            const simulationInterval = setInterval(() => {
                progress += (100 - progress) * 0.08; // asymptotic progression
                progressBar.style.width = progress + "%";

                if (progress < 25) {
                    currentPhase = 1;
                    loadingStep.textContent = "Idea Clarification: Drafting problem statement & audience profiles...";
                    setActiveIndicator(indClarify);
                } else if (progress < 48) {
                    currentPhase = 2;
                    setDoneIndicator(indClarify);
                    loadingStep.textContent = "Feasibility Analysis: Rating budget, timeline, and skill requirements...";
                    setActiveIndicator(indFeasibility);
                } else if (progress < 68) {
                    currentPhase = 3;
                    setDoneIndicator(indFeasibility);
                    loadingStep.textContent = "Risk Assessment: Spotting technical roadblocks and compiling mitigations...";
                    setActiveIndicator(indRisks);
                } else if (progress < 85) {
                    currentPhase = 4;
                    setDoneIndicator(indRisks);
                    loadingStep.textContent = "Scenario Simulation: Running optimistic, realistic, and pessimistic runs...";
                    setActiveIndicator(indScenarios);
                } else {
                    currentPhase = 5;
                    setDoneIndicator(indScenarios);
                    loadingStep.textContent = "Roadmap Generation: Setting up 30-60-90 day milestone milestones...";
                    setActiveIndicator(indRoadmap);
                }
            }, 300);

            // Make AJAX POST request to backend view
            fetch(form.action, {
                method: "POST",
                body: formData,
                headers: {
                    "X-Requested-With": "XMLHttpRequest"
                }
            })
            .then(response => response.json().then(data => ({ status: response.status, data })))
            .then(result => {
                clearInterval(simulationInterval);

                if (result.status === 200 && result.data.status === "success") {
                    // Complete loader
                    progressBar.style.width = "100%";
                    setDoneIndicator(indClarify);
                    setDoneIndicator(indFeasibility);
                    setDoneIndicator(indRisks);
                    setDoneIndicator(indScenarios);
                    setDoneIndicator(indRoadmap);
                    loadingStep.textContent = "Success! Plan forged. Redirecting to your dashboard...";

                    setTimeout(() => {
                        window.location.href = `/project/${result.data.project_id}/`;
                    }, 800);
                } else {
                    // Handle server validation / setup errors
                    overlay.classList.add("hidden");
                    
                    if (result.data.errors) {
                        // Field specific errors
                        Object.keys(result.data.errors).forEach(key => {
                            const errorSpan = document.getElementById(`error-${key}`);
                            if (errorSpan) {
                                errorSpan.textContent = result.data.errors[key];
                            }
                        });
                        showGlobalError("Please correct the errors in the form fields below.");
                    } else if (result.data.message) {
                        // Global message error (API key issues, exception, etc.)
                        showGlobalError(result.data.message);
                    } else {
                        showGlobalError("An unexpected error occurred. Please verify your connection and try again.");
                    }
                }
            })
            .catch(error => {
                clearInterval(simulationInterval);
                overlay.classList.add("hidden");
                console.error("Submission error:", error);
                showGlobalError("Failed to communicate with server. Please ensure the local database server is running.");
            });
        });
    }

    // Helper functions for loading indicators
    function setActiveIndicator(el) {
        if (!el) return;
        el.classList.add("active");
    }

    function setDoneIndicator(el) {
        if (!el) return;
        el.classList.remove("active");
        el.classList.add("done");
    }

    function showGlobalError(msg) {
        errorAlertText.textContent = msg;
        errorAlert.classList.remove("hidden");
        // Scroll to top of form card to show alert
        const card = document.querySelector(".form-container-card");
        if (card) {
            card.scrollIntoView({ behavior: "smooth" });
        }
    }

    // --- 5. GLOBAL DARK THEME TOGGLER ---
    console.log("DOMContentLoaded: Registering theme toggler...");
    const themeToggleBtn = document.getElementById("theme-toggle");
    console.log("themeToggleBtn element found:", themeToggleBtn);
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener("click", function () {
            console.log("Theme toggle button clicked!");
            const isDark = document.documentElement.classList.toggle("dark-theme");
            console.log("New theme state (isDark):", isDark);
            localStorage.setItem("theme", isDark ? "dark" : "light");
        });
    }
}

if (document.readyState === "interactive" || document.readyState === "complete") {
    initializeBrainForge();
} else {
    document.addEventListener("DOMContentLoaded", initializeBrainForge);
}
