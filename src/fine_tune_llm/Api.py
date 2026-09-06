from fastapi import FastAPI
from celery.result import AsyncResult
from .celery_app import celeryapp


app = FastAPI()



@app.post('/generate')

def generate(prompt:str):
    task = celeryapp.send_task('run_qwen',args=[prompt])
    return {
        'job_id':task.id,
        'status':'202 Accepted',
        'message':'job submitted Successfuly check /status/job_id for results!'


    }


@app.get('/status/{job_id}')

def get_job(job_id:str):
    result = AsyncResult(job_id, app=celeryapp)
    return{
        'job_id':job_id,
        'status':result.state,
        'result': result.result if result.ready() else None
    }
