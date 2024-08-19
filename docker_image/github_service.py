import os
#import requests
import logging
#from concurrent.futures import ThreadPoolExecutor,as_completed
from git import Repo
#from github import Github
#import shutil
from config.config import config
from dao.code_dao import Code_DAO


class github_service:
    def __init__(self, config:config):
        self.max_thread = 7
        
        work_dir = config.read('github', 'local_work_dir')
        token = config.read('github', 'access_token')
        
        self.token = token
        self.work_dir = work_dir
        
        self.logger = logging.getLogger(__name__)
        self.dao = Code_DAO(config)
        # Set environment variables for the Git operation
        os.environ['GIT_HTTP_LOW_SPEED_LIMIT'] = '1000'  # bytes per second
        os.environ['GIT_HTTP_LOW_SPEED_TIME'] = '30'     # seconds
        os.environ['GIT_HTTP_TIMEOUT'] = '60'
        
        # Create local directory if it doesn't exist
        os.makedirs(self.work_dir, mode=0o750, exist_ok=True)
        
    def clone(self, repo_owner:str, repo_name:str, ref:str):
        url = f"https://{self.token}@github.com/{repo_owner}/{repo_name}.git"
        try:
            location = os.path.join(self.work_dir, repo_owner, repo_name, ref)
            if os.path.exists(location) and os.listdir(location):
                repo = Repo(location)
                return (location, repo.head.object.hexsha)
            
            os.makedirs(location, mode=0o750, exist_ok=True)
            self.logger.debug(f"Start to clone {repo_owner}/{repo_name}/{ref} to {location}")
            repo = Repo.clone_from(url, location, depth = 1, branch=ref)
            #创建临时目录，下载完成后，再将临时目录名字修改为sha:
            #location = os.path.join(self.work_dir, repo_owner, repo_name, ref, "tmp")
            #new_location = os.path.join(self.work_dir, repo_owner, repo_name, ref, repo.head.object.hexsha)
            #os.rename(location, new_location)
            if not self.dao.add_code(repo_owner, repo_name, ref, repo.head.object.hexsha):
                self.logger.error(f"fail to save code:{repo_owner}/{repo_name}/{ref}")
            self.logger.debug(f"Successfully cloned {repo.head.object.hexsha} of {repo_owner}/{repo_name}/{ref} to {location}")
        except Exception as e:
            self.logger.error("fail to clone repository to local:", e)
            # shutil.rmtree(location)
            return (None, None)
        
        return (location, repo.head.object.hexsha)

    def get(self, repo_owner:str, repo_name:str, ref:str):
        return self.dao.get_code(repo_owner, repo_name, ref)
    
    # def clone1(self, repo_owner:str, repo_name:str, branch:str = None, tag:str = None):
    #     git = Github(self.token)
    #     try:
    #         # Get the repository
    #         repo = git.get_user(repo_owner).get_repo(repo_name)
            
    #         if tag is not None:
    #             tag = repo.get_git_ref(f"tags/{tag}")
    #             ref = tag.object.sha
    #         elif branch is not None:
    #             ref = branch
    #         else:
    #             # Get the default branch (usually 'main' or 'master')
    #             ref = repo.default_branch

    #         location = os.path.join(self.work_dir, repo_owner, repo_name, ref)
            
    #         os.makedirs(location, mode=0o750, exist_ok=True)
            
    #         # Get the contents of the repository at the root level
    #         contents = repo.get_contents("", ref=ref)
            
    #         # Start processing the repository contents
    #         self.__process_contents(contents, repo, ref, location)
    #     except Exception as e:
    #         self.logger.error("fail to clone repository to local:", e)
    #         return None
        
    #     return location
    
    # # Function to download files
    # def __download_file(self, file_content, dir):
    #     # Determine the local file path
    #     local_file_path = os.path.join(dir, file_content.path)
        
    #     # Make sure the parent directory exists
    #     os.makedirs(os.path.dirname(local_file_path), mode=0o750, exist_ok=True)
        
    #     response = requests.get(file_content.download_url, stream=True)
        
    #     # Download the file content
    #     with open(local_file_path, "wb") as file:
    #         for data in response.iter_content(chunk_size=1024):
    #             file.write(data)
            
    # # Function to process contents (files and directories)
    # def __process_contents(self, contents, repo, ref, dir):
    #     download_tasks = []
    #     while contents:
    #         content = contents.pop(0)
    #         if content.type == 'dir':
    #             # If it's a directory, get the contents and process them recursively
    #             new_contents = repo.get_contents(content.path, ref=ref)
    #             contents.extend(new_contents)
    #         else:
    #             # It's a file, download it
    #             download_tasks.append((content, dir))
        
    #     with ThreadPoolExecutor(max_workers=self.max_thread) as executor:
    #         futures = [executor.submit(self.__download_file, url, filename) for url, filename in download_tasks]
    #         for future in as_completed(futures):
    #             future.result()  # 这将重新引发任何异常