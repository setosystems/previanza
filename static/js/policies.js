document.addEventListener('DOMContentLoaded', (event) => {
    const policyForm = document.getElementById('policy-form');
    if (policyForm) {
        policyForm.addEventListener('submit', function(e) {
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
                    showFlashMessage('Póliza guardada exitosamente', 'success');
                    // Redirect to policy list or update the policy list
                    window.location.href = '/policies';
                } else {
                    showFlashMessage('Error al guardar la póliza', 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showFlashMessage('Ocurrió un error', 'error');
            });
        });
    }

    // Add event listener for premium calculation
    const premiumInput = document.getElementById('premium');
    const productSelect = document.getElementById('product_id');
    if (premiumInput && productSelect) {
        productSelect.addEventListener('change', function() {
            // This is a placeholder for premium calculation logic
            // In a real application, you might want to fetch the base premium from the server
            const basePremium = 1000; // Example base premium
            const productFactor = this.value / 10; // Example calculation factor
            premiumInput.value = (basePremium * productFactor).toFixed(2);
        });
    }
});
