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