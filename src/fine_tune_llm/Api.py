from pickletools import string4
import uuid
from fastapi import FastAPI, Header, HTTPException,status
from celery.result import AsyncResult
import upstash_redis
from .celery_app import celeryapp
import redis
import dotenv
import os
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from fastapi.requests import Request
from fastapi.responses import JSONResponse
import json

dotenv.load_dotenv()

url:str|None = os.getenv('UPSTASH_REDIS_REST_URL')

limiter = Limiter(key_func=get_remote_address ,storage_options={'redis':url} if url else {})

app = FastAPI()
if url is not None:

        redis_cli = redis.from_url(url)
else :
    raise ValueError("UPSTASH_REDIS_REST_URL environment variable is missing")
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={
            "status": 492,
            "error": "Rate limite reached"
        }
    )







@app.post('/generate')
@limiter.limit("5/minute")
def generate(request:Request,prompt:str, idempotency_key:str|None = Header(default = None)):
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
        data = redis_cli.get(f'job:{job_id}')
        return_json = json.loads(data) if data else None
        if return_json is not None :
            return  return_json
        result = AsyncResult(job_id, app=celeryapp)
        raw_data={
            'job_id':job_id,
            'status':result.state,
            'result': result.result if result.ready() else None
        }
        if result.state == 'SUCCESS':

            redis_cli.set(f'job:{job_id}', json.dumps(raw_data), ex=3600)

        return raw_data

    except Exception as e :
        return{
            'status':'500 Internal Server Error',
            'message':str(e)
        }
