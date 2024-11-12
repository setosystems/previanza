import openpyxl
from openpyxl import Workbook
import os

# Crear un nuevo libro de trabajo y seleccionar la hoja activa
wb = Workbook()
ws = wb.active

# Añadir los encabezados
ws.append([
    "Número de Póliza", "Fecha de Inicio", "Fecha de Fin", "Prima",
    "Número de Documento del Cliente", "Nombre del Producto",
    "Número de Documento del Agente", "Estado de Emisión", "Estado de Pago"
])

# Añadir datos de ejemplo
ws.append([
    "123456", "2023-01-01", "2023-12-31", "100.00",
    "987654321", "Seguro de Vida", "123456789", "Emitida", "Pagado"
])
ws.append([
    "654321", "2023-02-01", "2023-11-30", "200.00",
    "123456789", "Seguro de Auto", "987654321", "Pendiente", "Abonado"
])

# Asegúrate de que el directorio existe
output_dir = "static/samples"
os.makedirs(output_dir, exist_ok=True)

# Guardar el archivo
wb.save(os.path.join(output_dir, "polizas_ejemplo.xlsx"))
