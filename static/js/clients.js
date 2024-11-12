document.addEventListener('DOMContentLoaded', (event) => {
    const clientForm = document.getElementById('client-form');
    if (clientForm) {
        clientForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            fetch(this.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showFlashMessage('Cliente guardado exitosamente', 'success');
                    // Redirect to client list or update the client list
                    window.location.href = '/clients';
                } else {
                    showFlashMessage('Error al guardar el cliente', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showFlashMessage('Ocurrió un error', 'error');
            });
        });
    }
});
