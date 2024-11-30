#!/bin/sh
set -e

# Esperar a que la base de datos esté lista
echo "Esperando a la base de datos..."
while ! nc -z db 5432; do
  sleep 1
done

echo "Base de datos lista"

# Esperar a Redis
echo "Esperando a Redis..."
while ! nc -z redis 6379; do
  sleep 1
done

echo "Redis listo"

# Crear directorios necesarios
mkdir -p /app/static/uploads
mkdir -p /app/static/img/products
mkdir -p /app/static/samples
mkdir -p /app/reports
mkdir -p /app/migrations

# Establecer permisos
chown -R root:root /app/static
chmod -R 777 /app/static
chmod -R +t /app/static

# Inicializar la base de datos
export FLASK_APP=app.py
python -c "
from app import create_app, verify_database
app = create_app()
verify_database()
"

# Inicializar migraciones si no existen
if [ ! -d "migrations/versions" ]; then
    flask db init
    flask db migrate
    flask db upgrade
fi

# Crear usuario admin si no existe
flask create-admin admin admin@example.com password123 > /dev/null 2>&1 || true

# Generar archivos de ejemplo
python crea_excel.py || true

# Actualizar imágenes de productos
python update_product_images.py || true

# Iniciar la aplicación
exec "$@"
