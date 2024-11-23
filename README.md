<div align="center">

# 🏢 Sistema de Gestión de Seguros Previanza

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com)
[![License](https://img.shields.io/badge/License-Custom-blue.svg)](#licencia)

Sistema web profesional para la gestión integral de seguros, desarrollado con Flask y diseñado específicamente para empresas aseguradoras.

</div>

## 📋 Requisitos Previos

- Python 3.8+
- PostgreSQL 13+
- Node.js 20+
- Docker y Docker Compose
- Git

## 🚀 Instalación

### 1. Clonar el Repositorio
```bash
git clone <repositorio>
cd <directorio>
```

### 2. Configurar el Entorno
```bash
# Crear archivo .env
cp .env.example .env

# Editar variables de entorno según necesidad
nano .env
```

### 3. Iniciar con Docker
```bash
# Construir e iniciar contenedores
docker-compose up --build -d

# Ver logs
docker-compose logs -f
```

### 4. Verificar Servicios
- **Aplicación web**: http://localhost
- **Base de datos**: localhost:5432
- **Redis**: localhost:6379

### 5. Credenciales por Defecto
```
Usuario: admin
Email: admin@example.com
Contraseña: password123
```

### 6. Estructura de Directorios
El sistema creará automáticamente los siguientes directorios:
```
proyecto/
├── static/
│   ├── uploads/        # Archivos subidos
│   ├── img/products/   # Imágenes de productos
│   └── samples/        # Archivos de muestra
├── reports/           # Reportes generados
└── migrations/        # Migraciones de base de datos
```

### 7. Verificación
```bash
# Verificar el estado de los contenedores
docker-compose ps

# Verificar logs específicos
docker-compose logs web
docker-compose logs db
docker-compose logs nginx
```

### 8. Solución de Problemas
Si encuentras problemas durante la instalación:

```bash
# Detener y eliminar todos los contenedores y volúmenes
docker-compose down -v

# Limpiar sistema
docker system prune -a

# Reconstruir desde cero
docker-compose up --build -d
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
# PostgreSQL (recomendado)
DATABASE_URL = 'postgresql://usuario:contraseña@localhost/previanza'
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

## 🔐 Seguridad

- Autenticación basada en sesiones
- Protección CSRFd
- Validación de datos
- Encriptación de contraseñas
- Control de acceso por roles
- Sanitización de entradas
- Protección contra inyección SQL
- Headers de seguridad HTTP

## 🔄 Backup y Restauración

El sistema incluye scripts automatizados para backup:

```bash
# Ejecutar backup manual
./backup.sh

# Los backups se guardan en:
/backups/db_YYYYMMDD_HHMMSS.sql    # Base de datos
/backups/files_YYYYMMDD_HHMMSS.tar.gz  # Archivos
```

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

## 📞 Soporte

Para soporte técnico:
- Email: soporte@setosystems.com
- Teléfono: +593 XXXXXXXX
- Horario: Lunes a Viernes 9:00 - 18:00 (ECT)

## 🙏 Agradecimientos

* A todo el equipo de desarrollo
* A nuestros usuarios por su feedback
* A la comunidad de Flask y Python