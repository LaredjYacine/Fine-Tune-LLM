from celery import Celery
import os
import dotenv
dotenv.load_dotenv()
redis = os.getenv('UPSTASH_REDIS_REST_URL')
celeryapp = Celery('ai_agent',broker=redis , backend=redis)
