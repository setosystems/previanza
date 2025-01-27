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

# Verificar instalación de Node.js y npm
RUN node --version && npm --version

# Copiar archivos de requisitos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Crear directorios necesarios
RUN mkdir -p static/css \
    static/img/products \
    static/samples \
    reports \
    migrations

# Copiar archivos CSS y la imagen por defecto
COPY static/css/login.css static/css/
COPY static/css/input.css static/css/

# Establecer permisos
RUN chmod -R 755 static

# Configurar Tailwind CSS
COPY package*.json ./
RUN npm install

COPY tailwind.config.js .
COPY static/css/input.css static/css/input.css
COPY static/css/login.css static/css/login.css

# Generar CSS con Tailwind
RUN npx tailwindcss -i static/css/input.css -o static/css/output.css --minify

# Copiar el resto de la aplicación
COPY . .
COPY gunicorn_config.py /app/gunicorn_config.py

# Asegurarse de que los archivos CSS y la imagen por defecto existan y tengan los permisos correctos
RUN touch static/css/output.css && \
    chmod 644 static/css/output.css static/css/login.css

# Copiar y configurar la imagen por defecto
COPY static/img/products/default.jpg /app/static/img/products/
RUN chmod 644 /app/static/img/products/default.jpg

# Hacer ejecutable el script de entrada
COPY docker-entrypoint.sh /app/
RUN chmod +x /app/docker-entrypoint.sh

# Exponer puerto
EXPOSE 5000

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "wsgi:application"]