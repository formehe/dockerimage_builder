import os
import logging
from logging.handlers import RotatingFileHandler

class logfile:
    def __init__(self, log_dir:str):
        #log_dir = os.path.join(work_dir, "log")
        if not os.path.isdir(log_dir):
            os.makedirs(log_dir, mode=0o750, exist_ok=True)

        log_file = os.path.join(log_dir, "running.log")
        
        logging.basicConfig(
            handlers=[RotatingFileHandler(log_file, maxBytes=50000000, backupCount=10)],
            encoding='utf-8', 
            level=logging.DEBUG,
            format='%(thread)s %(asctime)s %(levelname)s %(message)s', 
            datefmt='%m/%d/%Y %I:%M:%S %p'
        )