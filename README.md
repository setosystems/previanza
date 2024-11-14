<div align="center">

# 🏢 Sistema de Gestión de Seguros

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com)
[![License](https://img.shields.io/badge/License-Custom-blue.svg)](#licencia)

Sistema web profesional para la gestión integral de seguros, desarrollado con Flask.

</div>

## ✨ Características Principales

### 👥 Gestión de Usuarios y Roles
- Roles diferenciados: Administrador, Digitador, Agente
- Sistema de autenticación seguro
- Control de acceso basado en roles
- Recuperación de contraseña por email

### 👥 Gestión de Clientes
- Registro y administración de clientes
- Validación de documentos de identidad
- Búsqueda avanzada y filtros
- Carga masiva desde Excel
- Historial completo de pólizas

### 📄 Gestión de Pólizas
- Creación y seguimiento de pólizas
- Asignación automática a agentes
- Control de estados de emisión y pagos
- Validaciones automáticas
- Carga masiva de pólizas

### 💰 Sistema de Comisiones
- Cálculo automático de comisiones
- Sobrecomisiones para supervisores
- Notificaciones por email
- Reportes detallados
- Configuración flexible de porcentajes

### 📊 Reportes y Análisis
- Dashboard interactivo
- Reportes personalizables
- Exportación a PDF y Excel
- Análisis de rendimiento
- Visualización de jerarquía de agentes

## 📋 Requisitos

- Python 3.8+
- PostgreSQL/SQLite
- Servidor SMTP para emails
- Dependencias en `requirements.txt`

## 🐳 Instalación con Docker

1. **Requisitos previos**
```bash
- Docker
- Docker Compose
```

2. **Configuración inicial**
```bash
# Clonar el repositorio
git clone <repositorio>
cd <directorio>

# Crear archivo .env
cp .env.example .env

# Crear directorios necesarios y establecer permisos
sudo mkdir -p static/img/products static/uploads
sudo chown -R $USER:$USER static/
sudo chmod -R 777 static/
sudo chmod -R +t static/
```

3. **Iniciar con Docker**
```bash
# Construir e iniciar contenedores
docker-compose up --build -d

# Ver logs
docker-compose logs -f
```

4. **Acceso**
- Aplicación web: http://localhost
- Base de datos: localhost:5433
- Redis: localhost:6379

5. **Credenciales por defecto**
```
Usuario: admin
Email: admin@example.com
Contraseña: password123
```

## 🛠️ Estructura del Proyecto Dockerizado

```
proyecto/
├── docker-compose.yml      # Configuración de servicios
├── Dockerfile             # Construcción de imagen web
├── nginx.conf            # Configuración de Nginx
├── docker-entrypoint.sh  # Script de inicialización
├── static/              # Archivos estáticos
│   ├── img/            # Imágenes
│   └── uploads/        # Archivos subidos
└── ...
```

## 🐋 Servicios Docker

- **web**: Aplicación Flask (Gunicorn)
- **db**: PostgreSQL
- **nginx**: Servidor web/proxy inverso
- **redis**: Caché y sesiones

## 📝 Logs y Debugging

```bash
# Ver logs de todos los servicios
docker-compose logs

# Ver logs de un servicio específico
docker-compose logs web
docker-compose logs db
docker-compose logs nginx
```

## 🔧 Mantenimiento

```bash
# Detener servicios
docker-compose down

# Reiniciar servicios
docker-compose restart

# Reconstruir servicios
docker-compose up --build -d
```

## 💻 Uso

1. **Iniciar el servidor**
   ```bash
   flask run
   ```

2. **Acceder a la aplicación**
   - Abrir navegador en `http://localhost:5000`
   - Iniciar sesión con las credenciales de administrador

## 🔧 Configuración

### Configuración de Email

```ini
MAIL_SERVER = 'smtp.tuservidor.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = 'tu@email.com'
MAIL_PASSWORD = 'tu-contraseña'
MAIL_DEFAULT_SENDER = 'tu@email.com'
```

### Configuración de Base de Datos

```ini
# SQLite (por defecto)
SQLALCHEMY_DATABASE_URI = 'sqlite:///app.db'

# PostgreSQL (opcional)
SQLALCHEMY_DATABASE_URI = 'postgresql://usuario:contraseña@localhost/basededatos'
```

## 📖 Documentación

### Estructura del Proyecto
```
sistema-seguros/
├── app.py              # Aplicación principal Flask
├── config.py           # Configuraciones
├── models.py           # Modelos de base de datos
├── forms.py            # Formularios WTForms
├── routes/            # Rutas de la aplicación
├── templates/         # Plantillas HTML
├── static/            # Archivos estáticos
└── utils/            # Utilidades y helpers
```

### Módulos Principales
- **auth**: Autenticación y gestión de usuarios
- **clients**: Gestión de clientes
- **policies**: Gestión de pólizas
- **agents**: Gestión de agentes
- **reports**: Reportes y análisis
- **config**: Configuraciones del sistema

## 🤝 Contribuir

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

Por favor, lee las [guías de contribución](CONTRIBUTING.md) antes de empezar.

## 📝 Licencia

Este proyecto está bajo una licencia personalizada. Ver el archivo [LICENSE](LICENSE) para más detalles.

## 👥 Autores

* **Seto Systems** - *Trabajo Inicial* - [usuario](https://github.com/usuario)