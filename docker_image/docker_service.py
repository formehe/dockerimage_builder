import docker
import logging
import re
import json
from config.config import config
from dao.image_dao import Image_DAO
from datetime import datetime, timedelta, timezone
from dateutil import parser

# Docker Hub用户名和仓库名
class docker_service:
    def __init__(self, config:config):
        username = config.read('docker_hub', 'registry_user_name')
        self.username = username
        self.client = docker.from_env(timeout = 10, max_pool_size = 5)
        self.logger = logging.getLogger(__name__)
        self.dao = Image_DAO(config)

    # {'stream': ' ---> e783c78dc428\n'}
    # {'stream': 'Step 2/15 : FROM ${BUILD_FROM}'}
    def build(self, tag, repository, dockerfile_dir, progress_callback, code_sha, build_args = None):
        image_name = f'{self.username.lower()}/{repository.lower()}:{tag}'
        build_info = []
        #task_detail = {"current_step":"", "total_steps":"", 'build_info':[]}
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        try:
            # 构建 Docker 镜像
            self.logger.debug("Building Docker image...")
            build_generator = self.client.api.build(
                path = dockerfile_dir, 
                tag = image_name, 
                buildargs = build_args,
                rm = True,
                forcerm = True,
                decode = True,
                timeout = 120)
                        
            for chunk in build_generator:
                if 'stream' in chunk:
                    self.logger.debug(chunk)
                    if chunk['stream'].startswith(("Compiling", "Listing")):
                        continue
                    for line in chunk['stream'].splitlines():
                        match = re.match(r"Step (\d+)/(\d+)", line)
                        if match:
                            progress_callback('current_step', match.group(1))
                            progress_callback('total_steps', match.group(2))
                        escape_line = ansi_escape.sub('', line)
                        # self.logger.debug(line)
                        if len(escape_line) != 0:
                            build_info.append(escape_line)
                elif 'error' in chunk:
                    build_info.append(chunk['error'])
                elif 'status' in chunk:
                    build_info.append(chunk['status'])
                progress_callback('build_info', build_info)
            # image, build_logs = self.client.images.build(path=dockerfile_dir, tag=image_name, buildargs = build_args)
            text = json.dumps(build_args)
            build_info = ''.join(build_info)
            if not self.dao.add_image(repository, tag, code_sha, text, build_info):
                self.logger.error(f"fail to save image: {repository}:{tag}, code_ref:{code_sha}")
        except docker.errors.BuildError as e:
            self.logger.error(f"Build failed: {e}")
            # 打印详细的错误信息
            for log in e.build_log:
                self.logger.error(log.get('stream', ''))
            self.logger.error(f"Error: {e}")
            return False
                
        return True
    
    #{'status': 'Preparing', 'progressDetail': {}, 'id': '84350733415d'}
    #{'status': 'Waiting', 'progressDetail': {}, 'id': 'b5cdd85e97ca'}
    #{'status': 'Pushing', 'progressDetail': {'current': 540160, 'total': 1015090788}, 'progress': '[> ]  540.2kB/1.015GB', 'id': 'c6885edc59d9'}
    #{'status': 'Pushed', 'progressDetail': {}, 'id': 'b7f5649b1645'}
    def publish(self, repository, tag, progress_callback):
        # 推送 Docker 镜像
        self.logger.debug("Pushing Docker image to Docker Hub...")
        repo = f'{self.username.lower()}/{repository.lower()}'
        #layers_progress = []
        publish_info = {}
        try:
            publish_generator = self.client.api.push(repo, tag=tag, stream=True, decode=True)
            
            total_count = len(list(publish_generator))
            complete_count = 0
            # 输出推送日志
            for chunk in publish_generator:
                if 'status' in chunk and 'id' in chunk:
                    layer_id = chunk['id']
                    if 'progress' in chunk:
                        publish_info[layer_id] = chunk['progress']
                    elif chunk['status'] == 'Layer already exists':
                        publish_info[layer_id] = 'Already exists'
                        complete_count += 1
                    elif chunk['status'] == 'Pushed':
                        publish_info[layer_id] = 'Pushed'
                        complete_count += 1
                    else:
                        publish_info[layer_id] = 'Doing'
                    progress_callback('publish_info', publish_info)
            
        except Exception as e:
            self.logger.error(f"Error pushing image: {e}")
            return False
        self.logger.debug("Docker image pushed successfully!")
        
        return True
    
    def get(self, repository, tag):
        try:
            image_name = f'{self.username.lower()}/{repository.lower()}:{tag}'
            image = self.client.images.get(image_name)
            image_detail = self.client.api.inspect_image(image.id)
        except Exception as e:
            self.logger.error(f"Error get image: {e}")
            return None
        return image_detail
    
    def delete(self, repository, tag):
        self.logger.debug("Deleting local Docker image")
        image_name = f'{self.username.lower()}/{repository.lower()}:{tag}'
        try:
            self.client.images.remove(image_name)
        except Exception as e:
            self.logger.error(f"Error pushing image: {e}")
            return False
        self.logger.debug("Local Docker image deleted")
        return True
    
    def clean(self):
        # 获取当前时间
        # 获取当前时间（UTC）
        now = datetime.now(timezone.utc)
        one_hour_ago = now - timedelta(hours = 24)
        # 获取所有镜像
        images = self.client.images.list()
        for image in images:
            self.logger.debug(f"image id:{image.id}, tag is:{image.tags}")
            try:
                if not image.tags:
                    created = parser.parse(image.attrs['Created'])
                    if created > one_hour_ago:
                        continue
                    self.client.images.remove(image.id, force=True)
                    self.logger.info(f"{image.id} is deleted")
            except Exception as e:
                self.logger.error(f"Error pushing image: {e}")