#!/bin/bash

# Configuración
BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Backup de la base de datos
docker-compose exec -T db pg_dump -U admin previanza > "${BACKUP_DIR}/db_${TIMESTAMP}.sql"

# Backup de archivos
tar -czf "${BACKUP_DIR}/files_${TIMESTAMP}.tar.gz" static/uploads static/img/products reports

# Mantener solo los últimos 7 backups
find ${BACKUP_DIR} -name "db_*.sql" -mtime +7 -delete
find ${BACKUP_DIR} -name "files_*.tar.gz" -mtime +7 -delete 