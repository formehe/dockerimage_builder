
from sqlalchemy import Column, String, UniqueConstraint, DateTime, TEXT
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Image_TBL(Base):
    __tablename__ = 'images'

    id = Column(String(128), primary_key=True)
    repo = Column(String(128), nullable=False)
    tag = Column(String(128), nullable=False)
    refer_sha = Column(String(128), nullable=False)
    build_param = Column(TEXT, nullable=True)
    build_info = Column(TEXT, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        UniqueConstraint('repo', 'tag', name = 'idx_repo_tag'),
    )

    def __repr__(self):
        return f"<Image(id={self.id}, repo={self.repo}, tag={self.tag})>"