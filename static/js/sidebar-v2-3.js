/* static/js/sidebar-v2-3.js */
document.addEventListener('DOMContentLoaded', () => {
    const sidebar = document.querySelector('.sidebar-v2-3');
    const toggleBtn = document.querySelector('.sidebar-toggle-btn');
    const closeBtn = document.querySelector('.sidebar-close');
    const overlay = document.querySelector('.sidebar-overlay');
    const navItems = document.querySelectorAll('.nav-item');

    const toggleSidebar = () => {
        sidebar.classList.toggle('open');
        overlay.classList.toggle('active');
    };

    if (toggleBtn) toggleBtn.onclick = toggleSidebar;
    if (closeBtn) closeBtn.onclick = toggleSidebar;
    if (overlay) overlay.onclick = toggleSidebar;

    // Navigation and Active state
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            // Remove active from others
            navItems.forEach(i => i.classList.remove('active'));
            item.classList.add('active');

            // Close sidebar on mobile after clicking
            if (window.innerWidth < 1024) {
                toggleSidebar();
            }

            // Here we would trigger the panel switch logic if we use the same as app.js
            // or just let the hash change handle it.
            const panel = item.getAttribute('data-panel');
            if (window.switchPanel && panel) {
                window.switchPanel(panel);
            }
        });
    });

    // Handle initial state / mobile
    if (window.innerWidth < 768) {
        console.log("LexDocsPro LITE: Mobile detectado - Sidebar colapsada.");
    }
});
