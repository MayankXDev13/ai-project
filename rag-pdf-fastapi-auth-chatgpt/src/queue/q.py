from redis import Redis
from rq import Queue
from src.config.config import REDIS_HOST, REDIS_PORT

redis_connection = Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=True,
)

queue = Queue(connection=redis_connection)
