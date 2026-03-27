#database shape-> This is exactly how the table looks inside Postgres.

from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from app.models.base import Base
from sqlalchemy import ForeignKey 
from sqlalchemy.orm import relationship 
from sqlalchemy import Float

class VaultItem(Base):
    __tablename__ = "vault_items"

    id = Column(Integer, primary_key=True, index=True)
    content_type = Column(String, nullable=False)
    title = Column(String, nullable=True)
    s3_key = Column(String, nullable=True)
    extracted_content = Column(Text, nullable=True)
    embedding = Column(Vector(384), nullable=True) # 384 is the MAGIC number for our model
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    chunks = relationship("VaultChunk", back_populates="parent")
    owner_id = Column(Integer, ForeignKey("users.id")) 
    owner = relationship("User", back_populates="items")

class VaultChunk(Base):
    __tablename__ = "vault_chunks"
    id = Column(Integer, primary_key=True, index=True)
    
    # WHAT: Which file does this chunk belong to?
    item_id = Column(Integer, ForeignKey("vault_items.id"))
    
    # WHAT: The actual text of this small piece
    content = Column(Text, nullable=False)
    
    # WHAT: The AI vector for THIS specific piece
    embedding = Column(Vector(384), nullable=True)
    
    parent = relationship("VaultItem", back_populates="chunks")

class AIRequestLog(Base):
    __tablename__ = "ai_logs"
    id = Column(Integer, primary_key=True, index=True)
    
    # WHAT: Which route was called? (/ask or /ingest?)
    endpoint = Column(String)
    
    # WHAT: How long did it take in seconds?
    # WHY: So we can find out where the "slowness" is.
    latency = Column(Float)
    
    # WHAT: Was it 200 (Success) or 500 (Error)?
    status_code = Column(Integer)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    
    # Link: One user has many vault items
    items = relationship("VaultItem", back_populates="owner")