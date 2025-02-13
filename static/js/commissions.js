// Inicializar los datos de productos
let products = [];
try {
    products = window.productsData || [];
} catch (e) {
    console.error('Error al inicializar datos de productos:', e);
}

// Función para cargar los valores de comisión cuando se cambia el producto
function loadCommissionValues(selectElement) {
    if (!selectElement) return;
    
    var agentId = selectElement.dataset.agentId;
    var productId = selectElement.value;
    var container = selectElement.closest('tr') || selectElement.closest('.bg-white\\/50');
    
    if (!container || !agentId || !productId) return;
    
    // Obtener los inputs
    var commissionInput = container.querySelector('.commission-input[data-agent-id="' + agentId + '"]');
    var sobrecomisionToggle = container.querySelector('.sobrecomision-toggle[data-agent-id="' + agentId + '"]');
    var overrideInput = container.querySelector('.override-percentage-input[data-agent-id="' + agentId + '"]');
    
    if (!commissionInput || !sobrecomisionToggle || !overrideInput) return;
    
    // Primero, mostrar los valores por defecto del producto como placeholder
    var product = products.find(function(p) { return p.id == productId; });
    if (product) {
        commissionInput.placeholder = 'Por defecto: ' + product.commission_percentage + '%';
        overrideInput.placeholder = 'Por defecto: ' + product.override_percentage + '%';
    }
    
    // Luego, buscar si hay valores personalizados
    fetch('/config/commissions/override/' + agentId + '/' + productId)
        .then(function(response) { return response.json(); })
        .then(function(data) {
            if (data.status === 'success' && data.commission_percentage !== null) {
                commissionInput.value = data.commission_percentage;
                overrideInput.value = data.override_percentage || '';
                sobrecomisionToggle.checked = data.sobrecomision;
                overrideInput.disabled = !data.sobrecomision;
            } else {
                // Si no hay valores personalizados, limpiar los inputs
                commissionInput.value = '';
                overrideInput.value = '';
                sobrecomisionToggle.checked = false;
                overrideInput.disabled = true;
            }
        })
        .catch(function(error) {
            console.error('Error al cargar valores personalizados:', error);
        });
}

// Función para manejar la visibilidad del campo de sobrecomisión
function toggleOverridePercentage(checkbox) {
    if (!checkbox) return;
    
    const row = checkbox.closest('tr');
    if (!row) return;
    
    const overrideInput = row.querySelector('.override-percentage-input, .override-input');
    if (!overrideInput) return;
    
    overrideInput.disabled = !checkbox.checked;
    if (!checkbox.checked) {
        overrideInput.value = '0';
    }
}

// Función para guardar comisión
function saveCommission(button) {
    if (!button) return;
    
    const productId = button.dataset.productId;
    if (!productId) {
        console.error('No se encontró el ID del producto');
        return;
    }
    
    const container = button.closest('tr') || button.closest('.bg-white\\/50');
    if (!container) {
        console.error('No se encontró el contenedor del producto');
        return;
    }
    
    const commissionInput = container.querySelector('.commission-input[data-product-id="' + productId + '"]');
    const sobrecomisionToggle = container.querySelector('.sobrecomision-toggle[data-product-id="' + productId + '"]');
    const overrideInput = container.querySelector('.override-percentage-input[data-product-id="' + productId + '"]');
    
    if (!commissionInput || !sobrecomisionToggle || !overrideInput) {
        console.error('No se encontraron todos los elementos necesarios');
        showMessage('error', 'Error: Faltan campos requeridos');
        return;
    }
    
    const data = {
        commission_percentage: commissionInput.value,
        sobrecomision: sobrecomisionToggle.checked,
        override_percentage: overrideInput.value
    };
    
    fetch('/config/commissions/product/' + productId, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams(data)
    })
    .then(function(response) {
        if (!response.ok) {
            throw new Error('Error en la respuesta del servidor: ' + response.status);
        }
        return response.json();
    })
    .then(function(data) {
        if (data.status === 'success') {
            showMessage('success', 'Comisión actualizada exitosamente');
        } else {
            showMessage('error', 'Error al actualizar la comisión: ' + (data.message || 'Error desconocido'));
        }
    })
    .catch(function(error) {
        console.error('Error al guardar la comisión:', error);
        showMessage('error', 'Error al guardar la comisión');
    });
}

// Función para guardar comisión de agente
function saveAgentCommission(button) {
    if (!button) return;
    
    const agentId = button.dataset.agentId;
    if (!agentId) {
        console.error('No se encontró el ID del agente');
        return;
    }
    
    const container = button.closest('tr') || button.closest('.bg-white\\/50');
    if (!container) {
        console.error('No se encontró el contenedor del agente');
        return;
    }
    
    const productSelect = container.querySelector('select[data-agent-id="' + agentId + '"]');
    const commissionInput = container.querySelector('.commission-input[data-agent-id="' + agentId + '"]');
    const sobrecomisionToggle = container.querySelector('.sobrecomision-toggle[data-agent-id="' + agentId + '"]');
    const overrideInput = container.querySelector('.override-percentage-input[data-agent-id="' + agentId + '"]');
    
    if (!productSelect || !commissionInput || !sobrecomisionToggle || !overrideInput) {
        console.error('No se encontraron todos los elementos necesarios');
        showMessage('error', 'Error: Faltan campos requeridos');
        return;
    }
    
    const data = {
        agent_id: agentId,
        product_id: productSelect.value,
        commission_percentage: commissionInput.value,
        sobrecomision: sobrecomisionToggle.checked,
        override_percentage: overrideInput.value
    };
    
    fetch('/config/commissions/override', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams(data)
    })
    .then(function(response) {
        if (!response.ok) {
            throw new Error('Error en la respuesta del servidor: ' + response.status);
        }
        return response.json();
    })
    .then(function(data) {
        if (data.status === 'success') {
            showMessage('success', 'Comisión personalizada actualizada exitosamente');
        } else {
            showMessage('error', 'Error al actualizar la comisión: ' + (data.message || 'Error desconocido'));
        }
    })
    .catch(function(error) {
        console.error('Error al guardar la comisión:', error);
        showMessage('error', 'Error al guardar la comisión');
    });
}

// Inicializar cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    try {
        // Inicializar los toggles de sobrecomisión
        document.querySelectorAll('.sobrecomision-toggle').forEach(function(checkbox) {
            toggleOverridePercentage(checkbox);
            checkbox.addEventListener('change', function() {
                toggleOverridePercentage(this);
            });
        });

        // Inicializar los botones de guardar
        document.querySelectorAll('.save-commission').forEach(function(button) {
            button.addEventListener('click', function() {
                if (this.dataset.productId) {
                    saveCommission(this);
                } else if (this.dataset.agentId) {
                    saveAgentCommission(this);
                }
            });
        });

        // Inicializar los selectores de producto y cargar valores iniciales
        document.querySelectorAll('select[data-agent-id]').forEach(function(select) {
            // Cargar valores iniciales
            loadCommissionValues(select);
            // Agregar listener para cambios
            select.addEventListener('change', function() {
                loadCommissionValues(this);
            });
        });

        // Cargar valores personalizados para agentes al inicio
        document.querySelectorAll('[data-agent-id]').forEach(function(element) {
            if (element.tagName === 'SELECT') {
                const agentId = element.dataset.agentId;
                const productId = element.value;
                if (agentId && productId) {
                    fetch('/config/commissions/override/' + agentId + '/' + productId)
                        .then(function(response) { return response.json(); })
                        .then(function(data) {
                            if (data.status === 'success' && data.commission_percentage !== null) {
                                const container = element.closest('tr') || element.closest('.bg-white\\/50');
                                if (container) {
                                    const commissionInput = container.querySelector('.commission-input[data-agent-id="' + agentId + '"]');
                                    const sobrecomisionToggle = container.querySelector('.sobrecomision-toggle[data-agent-id="' + agentId + '"]');
                                    const overrideInput = container.querySelector('.override-percentage-input[data-agent-id="' + agentId + '"]');

                                    if (commissionInput) commissionInput.value = data.commission_percentage;
                                    if (sobrecomisionToggle) sobrecomisionToggle.checked = data.sobrecomision;
                                    if (overrideInput) {
                                        overrideInput.value = data.override_percentage || '';
                                        overrideInput.disabled = !data.sobrecomision;
                                    }
                                }
                            }
                        })
                        .catch(function(error) {
                            console.error('Error al cargar valores personalizados:', error);
                        });
                }
            }
        });
    } catch (e) {
        console.error('Error al inicializar el módulo de comisiones:', e);
    }
});

// Función para mostrar mensajes
function showMessage(type, text) {
    const message = document.createElement('div');
    message.className = 'alert alert-' + type;
    Object.assign(message.style, {
        position: 'fixed',
        top: '20px',
        right: '20px',
        zIndex: '1000',
        padding: '15px',
        borderRadius: '5px',
        backgroundColor: type === 'success' ? '#d4edda' : '#f8d7da',
        color: type === 'success' ? '#155724' : '#721c24',
        border: '1px solid ' + (type === 'success' ? '#c3e6cb' : '#f5c6cb')
    });
    
    message.textContent = text;
    document.body.appendChild(message);

    setTimeout(function() {
        message.remove();
    }, 3000);
} 