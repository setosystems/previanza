// Inicializar los datos de productos
let products = window.productsData || [];

// Función para cargar los valores de comisión cuando se cambia el producto
function loadCommissionValues(selectElement) {
    var agentId = selectElement.dataset.agentId;
    var productId = selectElement.value;
    var row = selectElement.closest('tr');
    
    // Primero, mostrar los valores por defecto del producto
    var product = products.find(function(p) { return p.id == productId; });
    if (product) {
        row.querySelector('.commission-input').placeholder = 'Por defecto: ' + product.commission_percentage + '%';
        row.querySelector('.override-input').placeholder = 'Por defecto: ' + product.override_percentage + '%';
    }
    
    // Luego, buscar si hay valores personalizados
    fetch('/config/commissions/override/' + agentId + '/' + productId)
        .then(function(response) { return response.json(); })
        .then(function(data) {
            if (data.status === 'success') {
                if (data.commission_percentage !== null) {
                    row.querySelector('.commission-input').value = data.commission_percentage;
                    row.querySelector('.override-input').value = data.override_percentage;
                } else {
                    row.querySelector('.commission-input').value = '';
                    row.querySelector('.override-input').value = '';
                }
            }
        })
        .catch(function(error) {
            console.error('Error:', error);
        });
}

// Función para manejar la visibilidad del campo de sobrecomisión
function toggleOverridePercentage() {
    document.querySelectorAll('.sobrecomision-toggle').forEach(function(checkbox) {
        const row = checkbox.closest('tr');
        const overrideInput = row.querySelector('.override-percentage-input, .override-input');
        
        if (overrideInput) {
            overrideInput.style.display = checkbox.checked ? 'block' : 'none';
            if (!checkbox.checked) {
                overrideInput.value = '0';
            }
        }
    });
}

document.addEventListener('DOMContentLoaded', function() {
    // Inicializar los toggles existentes
    toggleOverridePercentage();
    
    // Agregar listeners para cambios futuros
    document.querySelectorAll('.sobrecomision-toggle').forEach(function(checkbox) {
        checkbox.addEventListener('change', toggleOverridePercentage);
    });

    // Guardar comisión de producto
    document.querySelectorAll('.save-commission').forEach(function(button) {
        button.addEventListener('click', function() {
            var productId = this.dataset.productId;
            var commissionInput = document.querySelector('.commission-input[data-product-id="' + productId + '"]');
            var sobrecomisionToggle = document.querySelector('.sobrecomision-toggle[data-product-id="' + productId + '"]');
            var overrideInput = document.querySelector('.override-percentage-input[data-product-id="' + productId + '"]');
            
            fetch('/config/commissions/product/' + productId, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    'commission_percentage': commissionInput.value,
                    'sobrecomision': sobrecomisionToggle.checked,
                    'override_percentage': overrideInput.value
                })
            })
            .then(function(response) { return response.json(); })
            .then(function(data) {
                if (data.status === 'success') {
                    showMessage('success', 'Comisión actualizada exitosamente');
                } else {
                    showMessage('error', 'Error al actualizar la comisión: ' + data.message);
                }
            })
            .catch(function(error) {
                console.error('Error:', error);
                showMessage('error', 'Error al actualizar la comisión');
            });
        });
    });

    // Inicializar los selectores de producto
    document.querySelectorAll('.product-select').forEach(function(select) {
        loadCommissionValues(select);
        select.addEventListener('change', function() {
            loadCommissionValues(this);
        });
    });
});

// Función para mostrar mensajes
function showMessage(type, text) {
    var message = document.createElement('div');
    message.className = 'alert alert-' + type;
    message.style.position = 'fixed';
    message.style.top = '20px';
    message.style.right = '20px';
    message.style.zIndex = '1000';
    message.style.padding = '15px';
    message.style.borderRadius = '5px';
    message.style.backgroundColor = type === 'success' ? '#d4edda' : '#f8d7da';
    message.style.color = type === 'success' ? '#155724' : '#721c24';
    message.style.border = '1px solid ' + (type === 'success' ? '#c3e6cb' : '#f5c6cb');
    message.innerHTML = '<i class="fas fa-' + (type === 'success' ? 'check' : 'exclamation') + '-circle"></i> ' + text;
    
    document.body.appendChild(message);

    setTimeout(function() {
        message.remove();
    }, 3000);
} 