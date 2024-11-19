function showDetails(agentId) {
    const startDate = document.getElementById('start_date').value;
    const endDate = document.getElementById('end_date').value;
    
    fetch(`/reports/agent/${agentId}/details?start_date=${startDate}&end_date=${endDate}`)
        .then(response => response.json())
        .then(data => {
            const modal = document.getElementById('detailsModal');
            const content = document.getElementById('detailsContent');
            
            let html = '<table class="min-w-full divide-y divide-gray-200">';
            html += `<thead class="bg-gray-50">
                        <tr>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fecha</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Póliza</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Producto</th>
                            <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Prima</th>
                            <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Comisión</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tipo</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Estado</th>
                            <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
                        </tr>
                    </thead>`;
            html += '<tbody class="bg-white divide-y divide-gray-200">';
            
            data.details.forEach(detail => {
                html += `<tr class="hover:bg-gray-50">
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${detail.date}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${detail.policy_number}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${detail.product_name}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">$${detail.premium.toLocaleString('es-CO', {minimumFractionDigits: 2})}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">$${detail.commission.toLocaleString('es-CO', {minimumFractionDigits: 2})}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${detail.commission_type}</td>
                    <td class="px-6 py-4 whitespace-nowrap">
                        <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                            ${detail.payment_status.toLowerCase() === 'pagado' ? 'bg-green-100 text-green-800' : 
                              detail.payment_status.toLowerCase() === 'pendiente' ? 'bg-yellow-100 text-yellow-800' : 
                              'bg-red-100 text-red-800'}">
                            ${detail.payment_status}
                        </span>
                    </td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <select class="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500" 
                                onchange="updateCommissionStatus(${detail.id}, this.value)">
                            <option value="">Cambiar estado</option>
                            <option value="PENDIENTE">Pendiente</option>
                            <option value="PAGADO">Pagado</option>
                            <option value="ANULADO">Anulado</option>
                        </select>
                    </td>
                </tr>`;
            });
            
            html += '</tbody></table>';
            content.innerHTML = html;
            modal.classList.remove('hidden');
        });
}

function updateCommissionStatus(commissionId, newStatus) {
    if (!newStatus) return;

    const formData = new FormData();
    formData.append('status', newStatus);

    fetch(`/reports/update_commission_status/${commissionId}`, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showDetails(currentAgentId); // Recargar los detalles
            location.reload(); // Recargar la página principal
        }
    });
}

// Cerrar modal
document.querySelector('.close').addEventListener('click', function() {
    document.getElementById('detailsModal').classList.add('hidden');
});

window.onclick = function(event) {
    const modal = document.getElementById('detailsModal');
    if (event.target == modal) {
        modal.classList.add('hidden');
    }
}

function exportToPDF() {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();
    
    doc.setFont('helvetica');
    doc.setFontSize(16);
    doc.text('Reporte de Comisiones', 14, 20);
    
    doc.setFontSize(12);
    const startDate = document.getElementById('start_date').value;
    const endDate = document.getElementById('end_date').value;
    doc.text(`Período: ${startDate} - ${endDate}`, 14, 30);
    
    doc.autoTable({
        html: 'table',
        startY: 40,
        theme: 'grid',
        headStyles: {
            fillColor: [44, 62, 80],
            textColor: 255,
            fontSize: 10
        },
        bodyStyles: {
            fontSize: 9
        },
        footStyles: {
            fillColor: [238, 238, 238],
            textColor: 0,
            fontSize: 10,
            fontStyle: 'bold'
        }
    });
    
    const fileName = `reporte-comisiones-${startDate}-${endDate}.pdf`;
    doc.save(fileName);
} 