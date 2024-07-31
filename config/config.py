import os
import configparser
import logging

class config:
    def __init__(self, path):
        # 创建一个配置解析器
        self.config = configparser.ConfigParser()
        self.logger = logging.getLogger(__name__)
        
        # 读取INI文件
        try:
            if os.path.isfile(path):
                self.config.read(path)
            else:
                self.logger("file is not exist.")
        except Exception as e:
            self.logger(f"{path} is not exist.")
    
    def read(self, module_name, key):
        try:
            return self.config[module_name][key]
        except Exception as e:
            self.logger(f"{key} of {module_name} is not exist.")