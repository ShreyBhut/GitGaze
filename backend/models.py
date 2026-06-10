import uuid
from datetime import datetime, UTC
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, JSON, Text
from sqlalchemy.orm import relationship
from .database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    path = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    
    snapshots = relationship("Snapshot", back_populates="project", cascade="all, delete-orphan")

class Snapshot(Base):
    __tablename__ = "snapshots"

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    status = Column(String, default="pending") # pending, processing, completed, failed
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    
    project = relationship("Project", back_populates="snapshots")
    file_nodes = relationship("FileNode", back_populates="snapshot", cascade="all, delete-orphan")

class FileNode(Base):
    __tablename__ = "file_nodes"

    id = Column(String, primary_key=True, default=generate_uuid)
    snapshot_id = Column(String, ForeignKey("snapshots.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String, nullable=False)
    content_hash = Column(String, nullable=False) # SHA-256
    node_type = Column(String, nullable=False) # file or dir
    metrics = Column(JSON, nullable=True) # LOC, SLOC, etc.
    
    snapshot = relationship("Snapshot", back_populates="file_nodes")

class AISummary(Base):
    __tablename__ = "ai_summaries"
    # Note: Not FK'd to file_nodes. This is a content-addressed cache

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String, nullable=False)
    content_hash = Column(String, nullable=False)
    summary_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))