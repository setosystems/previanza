document.addEventListener('DOMContentLoaded', (event) => {
    const salesChart = document.getElementById('sales-chart');
    const commissionChart = document.getElementById('commission-chart');

    if (salesChart) {
        // Fetch sales data and create a chart
        fetch('/reports/sales-data')
            .then(response => response.json())
            .then(data => {
                new Chart(salesChart, {
                    type: 'line',
                    data: {
                        labels: data.labels,
                        datasets: [{
                            label: 'Ventas',
                            data: data.values,
                            borderColor: 'rgb(75, 192, 192)',
                            tension: 0.1
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
            });
    }

    if (commissionChart) {
        // Fetch commission data and create a chart
        fetch('/reports/commission-data')
            .then(response => response.json())
            .then(data => {
                new Chart(commissionChart, {
                    type: 'bar',
                    data: {
                        labels: data.labels,
                        datasets: [{
                            label: 'Comisiones',
                            data: data.values,
                            backgroundColor: 'rgba(75, 192, 192, 0.6)'
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
            });
    }
});
