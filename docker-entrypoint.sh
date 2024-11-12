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

# Crear directorios necesarios si no existen y establecer permisos
mkdir -p /app/static/uploads
mkdir -p /app/static/img/products
mkdir -p /app/static/samples
mkdir -p /app/reports
mkdir -p /app/migrations

# Establecer permisos
chown -R root:root /app/static
chmod -R 777 /app/static
chmod -R +t /app/static

# Copiar env.py si no existe
if [ ! -f "migrations/env.py" ]; then
    echo "Copiando env.py..."
    cp /app/migrations/env.py migrations/env.py
fi

# Inicializar las migraciones dentro del contexto de la aplicación
python -c "
from app import create_app
app = create_app()
with app.app_context():
    from flask_migrate import init, migrate, upgrade
    from models import db
    db.create_all()
    try:
        init()
    except:
        pass
    migrate()
    upgrade()
"

# Crear usuario admin si no existe
export FLASK_APP=app.py
flask create-admin admin admin@example.com password123

# Generar archivos de ejemplo
python crea_excel.py

# Actualizar imágenes de productos
python update_product_images.py

# Iniciar la aplicación
exec "$@" 