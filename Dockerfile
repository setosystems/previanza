# Imagen base
FROM python:3.8-slim

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema incluyendo netcat para health checks
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    gcc \
    python3-dev \
    libjpeg-dev \
    zlib1g-dev \
    netcat-openbsd \
    wkhtmltopdf \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primero
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Crear directorios necesarios
RUN mkdir -p static/uploads \
    static/img/products \
    static/samples \
    reports \
    migrations

# Copiar el código
COPY . .

# Hacer ejecutable el script de entrada
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Exponer puerto
EXPOSE 5000

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "wsgi:application"] 