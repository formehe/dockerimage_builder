import threading
import time
from typing import Dict
from pydantic import BaseModel
from uuid import uuid4
import argparse
import logging
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import JSONResponse
import uvicorn
from docker_image.docker_service import docker_service
from docker_image.github_service import github_service
from config.config import config
from logfile.logfile import logfile


app = FastAPI(
    title="the pipeline of making container image",
    description="""downloading dockerfile、build container image and push image""",
    version="0.0.1",
    docs_url="/",
)

class image_build_publish_info(BaseModel):
    # github info
    code_repo_owner_name:str
    code_repo_name:str
    code_ref: str
    
    #container image info
    image_repo:str
    image_tag:str
    image_args: Dict[str, str]

def build_and_publish(info: image_build_publish_info, task_id: str):
    logger.info(f"run task:{task_id}, code:{info.code_repo_owner_name}:{info.code_repo_name}, image:{info.image_repo.lower()}:{info.image_tag.lower()}")
    tasks[task_id]['name']  = f'{info.image_repo.lower()}:{info.image_tag.lower()}'
    tasks[task_id]['stage'] = "downloading"
    location, sha = git_srv.clone(info.code_repo_owner_name, info.code_repo_name,  info.code_ref)
    if location is None:
        tasks[task_id]['stage'] = "failed download"
        return False
    tasks[task_id]['stage'] = "building"
    if not docker_srv.build(info.image_tag, info.image_repo, location, lambda key, value: update_task_status(task_id, key, value), sha, info.image_args):
        tasks[task_id]['stage'] = "failed build"
        return False
    tasks[task_id]['stage'] = "publishing"
    if not docker_srv.publish(info.image_repo, info.image_tag, lambda key, value: update_task_status(task_id, key, value)):
        tasks[task_id]['stage'] = "failed publish"
        return False
    tasks[task_id]['stage'] = "completed"
    logger.info(f"finish task:{task_id}")
    return True

tasks = {}

def update_task_status(task_id: str, key:str, value: str):
    tasks[task_id]['detail'][key] = value

@app.post("/run-task")
async def run_task(info: image_build_publish_info, background_tasks: BackgroundTasks):
    task_id = str(uuid4())
    
    tasks[task_id]= {
        'name': f'{info.image_repo.lower()}:{info.image_tag.lower()}', 
        'stage':'beginning', 
        'detail':{}}
    background_tasks.add_task(build_and_publish, info, task_id)
    return {"task_id": task_id}

@app.get("/task-status/{task_id}")
async def task_status(task_id: str):
    status = tasks.get(task_id, "not found")
    return {"task_id": task_id, "status": status}

@app.get("/image/{repository}/{tag}")
async def get_image(repository: str, tag: str):
    image_detail = docker_srv.get(repository, tag)
    if image_detail:
        return JSONResponse(content=image_detail)
    return None

@app.get("/code/{owner}/{repo}/{ref}")
async def get_code(owner: str, repo: str, ref: str):
    code_detail = git_srv.get(owner, repo, ref)
    if code_detail:
        return code_detail.as_dict() 
    return None

def recycle():
    while True:
        docker_srv.clean()
        time.sleep(86400)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='启动参数')

    # 添加命令行选项
    parser.add_argument(
        '--config', 
        type = str,
        required=True,
        help='配置路径位置'
    )
    
    logger = logging.getLogger(__name__)
    
    # 解析命令行参数
    args = parser.parse_args()
    config = config(args.config)
    log_dir = config.read('log', 'local_log_dir')
    
    git_srv = github_service(config)
    docker_srv = docker_service(config)
    
    logfile(log_dir)
    
    # 创建后台线程来执行清理任务
    cleaning_thread = threading.Thread(target=recycle)
    cleaning_thread.daemon = True
    cleaning_thread.start()
    
    uvicorn.run(
        app,
        host=config.read('server', 'host'),
        port=int(config.read('server', 'port')),
        #ssl_keyfile  = "key.pem",
        #ssl_certfile = "cert.pem"
    )