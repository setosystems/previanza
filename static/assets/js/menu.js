document.addEventListener('DOMContentLoaded', function() {
    // Variables globales
    const layoutWrapper = document.querySelector('.layout-wrapper');
    const menuItems = document.querySelectorAll('.menu-item');

    // Función para manejar el menú colapsable
    function handleCollapsibleMenu() {
        const collapseTrigger = document.getElementById('collapse-trigger');
        
        if (collapseTrigger) {
            collapseTrigger.addEventListener('click', () => {
                layoutWrapper.classList.toggle('collapsed');
                
                // Guardar el estado en localStorage
                const isCollapsed = layoutWrapper.classList.contains('collapsed');
                localStorage.setItem('sidebarCollapsed', isCollapsed);
            });
            
            // Restaurar el estado al cargar la página
            const wasCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
            if (wasCollapsed) {
                layoutWrapper.classList.add('collapsed');
            }
        }
    }

    // Función para manejar el menú móvil
    function handleMobileMenu() {
        const mobileMenuTrigger = document.querySelector('.layout-menu-toggle');
        
        if (mobileMenuTrigger) {
            mobileMenuTrigger.addEventListener('click', () => {
                layoutWrapper.classList.toggle('layout-menu-expanded');
            });
        }
    }

    // Función para manejar los dropdowns del menú
    function handleMenuDropdowns() {
        menuItems.forEach(item => {
            const link = item.querySelector('.menu-link');
            const submenu = item.querySelector('.menu-sub');
            
            if (submenu) {
                link.addEventListener('click', (e) => {
                    e.preventDefault();
                    
                    // Toggle active class
                    item.classList.toggle('active');
                    
                    // Manejar la altura del submenu
                    if (item.classList.contains('active')) {
                        submenu.style.maxHeight = submenu.scrollHeight + "px";
                    } else {
                        submenu.style.maxHeight = "0px";
                    }
                    
                    // Cerrar otros submenús abiertos
                    menuItems.forEach(otherItem => {
                        if (otherItem !== item && otherItem.classList.contains('active')) {
                            otherItem.classList.remove('active');
                            const otherSubmenu = otherItem.querySelector('.menu-sub');
                            if (otherSubmenu) {
                                otherSubmenu.style.maxHeight = "0px";
                            }
                        }
                    });
                });
            }
        });
    }

    // Función para manejar hover en modo colapsado
    function handleCollapsedHover() {
        menuItems.forEach(item => {
            const submenu = item.querySelector('.menu-sub');
            if (submenu) {
                item.addEventListener('mouseenter', () => {
                    if (layoutWrapper.classList.contains('collapsed')) {
                        submenu.style.maxHeight = submenu.scrollHeight + "px";
                        item.classList.add('showing');
                    }
                });
                
                item.addEventListener('mouseleave', () => {
                    if (layoutWrapper.classList.contains('collapsed')) {
                        submenu.style.maxHeight = "0px";
                        item.classList.remove('showing');
                    }
                });
            }
        });
    }

    // Inicializar Perfect Scrollbar
    function initPerfectScrollbar() {
        const menuInner = document.querySelector('.menu-inner');
        if (menuInner) {
            new PerfectScrollbar(menuInner);
        }
    }

    // Mantener abierto el menú activo al cargar
    function keepActiveMenuOpen() {
        const activeMenuItem = document.querySelector('.menu-item.active');
        if (activeMenuItem) {
            const activeSubmenu = activeMenuItem.querySelector('.menu-sub');
            if (activeSubmenu) {
                activeSubmenu.style.maxHeight = activeSubmenu.scrollHeight + "px";
            }
        }
    }

    // Inicializar todas las funcionalidades
    handleCollapsibleMenu();
    handleMobileMenu();
    handleMenuDropdowns();
    handleCollapsedHover();
    initPerfectScrollbar();
    keepActiveMenuOpen();
}); 