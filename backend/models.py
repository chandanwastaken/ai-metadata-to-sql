from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from db import Base
from datetime import datetime
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default='analyst', nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    histories = relationship('QueryHistory', back_populates='user')
class QueryHistory(Base):
    __tablename__ = 'query_history'
    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    sql = Column(Text, nullable=False)
    schema = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship('User', back_populates='histories')
class TokenBlacklist(Base):
    __tablename__ = 'token_blacklist'
    id = Column(Integer, primary_key=True, index=True)
    token = Column(Text, nullable=False, unique=True)
    expires_at = Column(DateTime, nullable=True)
