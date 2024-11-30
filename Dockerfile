# Imagen base
FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema y Node.js
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    gcc \
    python3-dev \
    libjpeg-dev \
    zlib1g-dev \
    netcat-openbsd \
    wkhtmltopdf \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g tailwindcss \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primero
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Crear directorios necesarios
RUN mkdir -p static/css \
    static/img/products \
    static/samples \
    reports \
    migrations

# Copiar archivos estáticos
COPY static/css/login.css static/css/
COPY static/css/input.css static/css/

# Asegurar permisos correctos
RUN chmod -R 755 static

# Inicializar npm y crear package.json
RUN npm init -y && \
    npm install -D @tailwindcss/forms

# Copiar archivos de configuración de Tailwind y CSS
COPY tailwind.config.js .
COPY static/css/input.css static/css/input.css
COPY static/css/login.css static/css/login.css

# Compilar Tailwind CSS
RUN npx tailwindcss -i static/css/input.css -o static/css/output.css --minify

# Copiar el resto del código
COPY . .
COPY gunicorn_config.py /app/gunicorn_config.py

# Asegurarse de que los archivos CSS existan y tengan los permisos correctos
RUN touch static/css/output.css && \
    chmod 644 static/css/output.css static/css/login.css

# Hacer ejecutable el script de entrada
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Exponer puerto
EXPOSE 5000

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "wsgi:application"]