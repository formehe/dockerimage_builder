
from sqlalchemy import Column, String, UniqueConstraint, DateTime
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Code_TBL(Base):
    __tablename__ = 'codes'

    id = Column(String(128), primary_key=True)
    owner = Column(String(128), nullable=False)
    repo = Column(String(128), nullable=False)
    ref = Column(String(128), nullable=False)
    sha = Column(String(128), nullable=False)
    
    created_at = Column(DateTime, default = func.now())
    updated_at = Column(DateTime, default = func.now(), onupdate = func.now())

    __table_args__ = (
        UniqueConstraint('sha', name = 'idx_sha'),
        UniqueConstraint('owner', 'repo', 'ref', name = 'idx_owner_repo_ref'),
    )
    
    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    
    def __repr__(self):
        return f"<codes(owner={self.owner}, repo={self.repo}, ref={self.ref}, sha={self.sha})>"