document.addEventListener('DOMContentLoaded', function() {
    // Inicializar Perfect Scrollbar en el menú
    const menuInner = document.querySelector('.menu-inner');
    if (menuInner) {
        new PerfectScrollbar(menuInner);
    }

    // Toggle del menú en móvil
    const menuToggle = document.querySelector('.layout-menu-toggle');
    const layout = document.querySelector('.layout-wrapper');
    
    if (menuToggle) {
        menuToggle.addEventListener('click', () => {
            layout.classList.toggle('layout-menu-expanded');
        });
    }
}); 