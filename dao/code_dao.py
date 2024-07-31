import logging
from sqlalchemy import create_engine,exc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import reflection
from dao.code_tbl import *
from config.config import config
from toollib.guid import SnowFlake

class Code_DAO:
    def __init__(self, config:config) -> None:
        DATABASE_URL = """mysql+pymysql://{}:{}@{}:{}/{}?connect_timeout=10""".format(
                            config.read("mysql", "user"),
                            config.read("mysql", "password"),
                            config.read("mysql", "host"),
                            config.read("mysql", "port"),
                            config.read("mysql", "db_name"))
        self.logger = logging.getLogger(__name__)
        self.engine = create_engine(DATABASE_URL, echo = True, pool_pre_ping = True, pool_recycle = -1)
        #logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)  # 设置日志级别为 INFO 或 DEBUG
        
        if not reflection.Inspector.from_engine(self.engine).has_table(Code_TBL.__tablename__):
            Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        self.generator = SnowFlake()
        
    def add_code(self, code_owner, code_repo, ref, sha):
        try:
            existing_record = self.session.query(Code_TBL).filter(Code_TBL.sha == sha).first()
            if not existing_record:
                new_content = Code_TBL(id = self.generator.gen_uid(), owner=code_owner, repo=code_repo, ref = ref, sha=sha)
                self.session.add(new_content)
                self.session.commit()

            return True
        except exc.OperationalError as e:
            self.logger.error("fail to add code:", e)
            self.engine.dispose()  # 释放连接
            self.session = self.Session()
        
        return False

    def get_code(self, owner, repo, ref):
        try:
            return self.session.query(Code_TBL).filter(Code_TBL.owner == owner, Code_TBL.repo == repo, Code_TBL.ref == ref).first()
        except exc.OperationalError as e:
            self.logger.error("fail to get code:", e)
            self.engine.dispose()  # 释放连接
            self.session = self.Session()
        return None

    def delete_code(self, id):
        try:
            content = self.session.query(Code_TBL).filter(Code_TBL.id == id).first()
            if content:
                self.session.delete(content)
                self.session.commit()
                return True
        except exc.OperationalError as e:
            self.logger.error("fail to delete code:", e)
            self.engine.dispose()  # 释放连接
            self.session = self.Session()
        return False