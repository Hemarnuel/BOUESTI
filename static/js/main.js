document.addEventListener("DOMContentLoaded", function () {
    // Auto-dismiss alerts after 5 seconds
    document.querySelectorAll(".alert").forEach(function (alertEl) {
        setTimeout(function () {
            const alert = bootstrap.Alert.getOrCreateInstance(alertEl);
            if (alert) alert.close();
        }, 5000);
    });

    // Confirm before destructive actions (e.g. delete job)
    document.querySelectorAll("[data-confirm]").forEach(function (el) {
        el.addEventListener("submit", function (e) {
            if (!confirm(el.getAttribute("data-confirm"))) {
                e.preventDefault();
            }
        });
    });
});
