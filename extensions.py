from flask_mail import Mail
from rq import Queue
from redis import Redis

mail = Mail()
redis_conn = Redis(host='redis', port=6379)
task_queue = Queue(connection=redis_conn)
