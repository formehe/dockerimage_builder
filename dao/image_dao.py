import logging
import os
from sqlalchemy import create_engine,exc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import reflection
from dao.image_tbl import *
from config.config import config
from toollib.guid import SnowFlake

class Image_DAO:
    def __init__(self, config:config) -> None:
        HOST = os.getenv("IMAGE_BUILDER_DATABASE_SERVICE_HOST", None)
        if HOST is None:
            HOST = config.read("mysql", "host")
        PORT = os.getenv("IMAGE_BUILDER_DATABASE_SERVICE_PORT", None)
        if PORT is None:
            PORT = config.read("mysql", "port")
        DATABASE_URL = """mysql+pymysql://{}:{}@{}:{}/{}?connect_timeout=10""".format(
                            config.read("mysql", "user"),
                            config.read("mysql", "password"),
                            HOST,
                            PORT,
                            config.read("mysql", "db_name"))
        self.logger = logging.getLogger(__name__)
        self.engine = create_engine(DATABASE_URL, echo = True, pool_pre_ping = True, pool_recycle = -1)
        #logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)  # 设置日志级别为 INFO 或 DEBUG
        if not reflection.Inspector.from_engine(self.engine).has_table(Image_TBL.__tablename__):
            Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        self.generator = SnowFlake()

    def add_image(self, repo, tag, refer_sha, build_param, build_info):
        try:
            existing_record = self.session.query(Image_TBL).filter(Image_TBL.repo == repo, Image_TBL.tag == tag).first()
            if not existing_record:
                new_content = Image_TBL(id = self.generator.gen_uid(), repo = repo, tag = tag, refer_sha = refer_sha, build_param = build_param, build_info=build_info)
                self.session.add(new_content)
                self.session.commit()
            return True
        except exc.OperationalError as e:
            self.logger.error("fail to add image:", e)
            self.engine.dispose()  # 释放连接
            self.session = self.Session()
        
        return False

    def get_image(self, repo, tag):
        try:
            return self.session.query(Image_TBL).filter(Image_TBL.repo == repo, Image_TBL.tag == tag).first()
        except exc.OperationalError as e:
            self.logger.error("fail to get image:", e)
            self.engine.dispose()  # 释放连接
            self.session = self.Session()
        
        return None

    def delete_image(self, id):
        try:
            content = self.session.query(Image_TBL).filter(Image_TBL.id == id).first()
            if content:
                self.session.delete(content)
                self.session.commit()
                return True
        except exc.OperationalError as e:
            self.logger.error("fail to delete image:", e)
            self.engine.dispose()  # 释放连接
            self.session = self.Session()
        return False