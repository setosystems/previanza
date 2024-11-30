# Configuración básica
bind = "0.0.0.0:5000"
workers = 4
worker_class = "sync"
timeout = 120

# Configuración de logs
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Configuración de worker
worker_tmp_dir = "/dev/shm"
max_requests = 1000
max_requests_jitter = 50

# Configuración de timeout
graceful_timeout = 120
keepalive = 5

def worker_int(worker):
    """Asigna un ID único a cada worker"""
    worker.cfg.env["FLASK_APP_WORKER_ID"] = str(worker.age + 1)

def on_starting(server):
    """Se ejecuta cuando el servidor está iniciando"""
    server.log.info("Configurando workers con IDs...") 