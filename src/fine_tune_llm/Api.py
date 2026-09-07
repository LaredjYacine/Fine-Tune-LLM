from pickletools import string4
import uuid
from fastapi import FastAPI, Header
from celery.result import AsyncResult
from .celery_app import celeryapp
import redis
import dotenv
import os
dotenv.load_dotenv()

url:str|None = os.getenv('UPSTASH_REDIS_REST_URL')


app = FastAPI()
if url is not None:

        redis_cli = redis.from_url(url)
else :
    print('url is not Logged Check your enviornment')

@app.post('/generate')

def generate(prompt:str, idempotency_key:str|None = Header(default = None)):
    try :
        if idempotency_key is None:
            idempotency_key = str(uuid.uuid4())

        claimed = redis_cli.set(
            f'idem_job:{idempotency_key}',
            'pending',
            nx=True,
            ex=86400
        )
        if not claimed :

            existing_job_id = redis_cli.get(f'idem_job:{idempotency_key}')
            existing_job_id = existing_job_id.decode() if existing_job_id else None

            return {
                'job_id':existing_job_id,
                'status':'duplicate',
                'idempotency_key':idempotency_key,
                'message':'job was already submitted before !'
            }

        task = celeryapp.send_task('run_qwen',args=[prompt])
        redis_cli.set(f"idem_job:{idempotency_key}", task.id, ex=86400)
        return {
            'job_id':task.id,
            'status':'202 Accepted',
            'idempotency_key':idempotency_key,
            'message':'job submitted Successfuly check /status/job_id for results!'
        }
    except Exception as e :
        return{
            'status':'500 Internal Server Error',
            'message':str(e)
        }


@app.get('/status/{job_id}')

def get_job(job_id:str):
    try  :

        result = AsyncResult(job_id, app=celeryapp)
        return{
            'job_id':job_id,
            'status':result.state,
            'result': result.result if result.ready() else None
        }
    except Exception as e :
        return{
            'status':'500 Internal Server Error',
            'message':str(e)
        }
