document.addEventListener('DOMContentLoaded', function() {
    // Elementos del DOM
    const menuToggle = document.getElementById('menu-toggle');
    const sidebar = document.querySelector('.sidebar');
    const container = document.querySelector('.container');
    const dropdownButtons = document.querySelectorAll('.dropbtn');
    
    // Crear el overlay
    let overlay = document.querySelector('.overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.className = 'overlay';
        document.body.appendChild(overlay);
    }

    // Función para alternar el menú
    function toggleMenu() {
        sidebar.classList.toggle('active');
        overlay.classList.toggle('active');
    }

    // Event listener para el botón de menú
    if (menuToggle) {
        menuToggle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            toggleMenu();
        });
    }

    // Cerrar el menú al hacer clic en el overlay
    overlay.addEventListener('click', function() {
        if (sidebar.classList.contains('active')) {
            toggleMenu();
        }
    });

    // Manejar los dropdowns
    const dropdowns = document.querySelectorAll('.dropdown');
    dropdowns.forEach(dropdown => {
        const button = dropdown.querySelector('.dropbtn');
        button.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            // Cerrar otros dropdowns
            dropdowns.forEach(otherDropdown => {
                if (otherDropdown !== dropdown) {
                    otherDropdown.classList.remove('active');
                }
            });
            
            // Toggle el dropdown actual
            dropdown.classList.toggle('active');
        });
    });

    // Cerrar dropdowns cuando se hace clic fuera
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.dropdown')) {
            dropdowns.forEach(dropdown => {
                dropdown.classList.remove('active');
            });
        }
    });

    // Cerrar el menú solo cuando se hace clic en enlaces que no son dropdowns
    const menuLinks = sidebar.querySelectorAll('a:not(.dropbtn)');
    menuLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            if (window.innerWidth <= 768 && !this.classList.contains('dropbtn')) {
                toggleMenu();
            }
        });
    });

    // Mantener el dropdown abierto cuando se hace clic dentro
    const dropdownContents = document.querySelectorAll('.dropdown-content');
    dropdownContents.forEach(content => {
        content.addEventListener('click', function(e) {
            e.stopPropagation();
        });
    });

    // Manejo de formularios
    const forms = document.querySelectorAll('.modern-form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;

            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    field.classList.add('error');
                } else {
                    field.classList.remove('error');
                }
            });

            if (!isValid) {
                e.preventDefault();
                showFlashMessage('Por favor, complete todos los campos requeridos', 'error');
            }
        });
    });

    // Agregar al archivo main.js existente
    function showLoading(button) {
        const originalText = button.innerHTML;
        button.classList.add('loading');
        button.disabled = true;
        return originalText;
    }

    function hideLoading(button, originalText) {
        button.classList.remove('loading');
        button.disabled = false;
        button.innerHTML = originalText;
    }

    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitButton = this.querySelector('[type="submit"]');
            if (submitButton) {
                const originalText = showLoading(submitButton);
                setTimeout(() => hideLoading(submitButton, originalText), 1000);
            }
        });
    });
});

function showFlashMessage(message, type = 'info') {
    const flashContainer = document.getElementById('flash-messages');
    const flashMessage = document.createElement('div');
    flashMessage.textContent = message;
    flashMessage.className = `flash ${type}`;
    flashContainer.appendChild(flashMessage);

    setTimeout(() => {
        flashMessage.remove();
    }, 5000);
}
