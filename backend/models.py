import uuid
from datetime import datetime, UTC
from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime, JSON, Text, UniqueConstraint, Boolean
from sqlalchemy.orm import relationship
from database import Base


def generate_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    github_id = Column(String, unique=True, nullable=False)
    username = Column(String, nullable=False)
    avatar_url = Column(String, nullable=True)
    access_token = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    projects = relationship("Project", back_populates="user")


class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    github_url = Column(String, nullable=False, unique=True)
    path = Column(String, nullable=False)
    is_private = Column(Boolean, default=False)
    user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    user = relationship("User", back_populates="projects")
    snapshots = relationship("Snapshot", back_populates="project", cascade="all, delete-orphan")
    config = relationship("AnalysisConfig", back_populates="project", uselist=False, cascade="all, delete-orphan")


class AnalysisConfig(Base):
    """
    Per-project analysis configuration.
    Stores which directories to exclude, file size limits, and enabled languages.
    One-to-one with Project.
    """
    __tablename__ = "analysis_config"

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, unique=True)

    # JSON lists, e.g. ["tests", "docs"] or [".py", ".js"]
    excluded_dirs = Column(JSON, nullable=False, default=list)
    enabled_languages = Column(JSON, nullable=False, default=list)

    # Maximum file size to parse in KB (skip files larger than this)
    max_file_size_kb = Column(Integer, nullable=False, default=500)

    project = relationship("Project", back_populates="config")


class Snapshot(Base):
    __tablename__ = "snapshots"

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    status = Column(String, default="pending")  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)  # populated when status == "failed"
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    completed_at = Column(DateTime, nullable=True)

    project = relationship("Project", back_populates="snapshots")
    file_nodes = relationship("FileNode", back_populates="snapshot", cascade="all, delete-orphan")
    dependency_edges = relationship("DependencyEdge", back_populates="snapshot", cascade="all, delete-orphan")


class FileNode(Base):
    __tablename__ = "file_nodes"

    id = Column(String, primary_key=True, default=generate_uuid)
    snapshot_id = Column(String, ForeignKey("snapshots.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String, nullable=False)   # relative path from repo root, forward slashes
    content_hash = Column(String, nullable=False)  # SHA-256 hex digest
    node_type = Column(String, nullable=False)     # "file" or "dir"
    language = Column(String, nullable=True)        # detected language extension, e.g. ".py"
    metrics = Column(JSON, nullable=True)           # {loc, sloc, comments, blanks}
    imports = Column(JSON, nullable=True)           # list of raw import strings
    functions = Column(JSON, nullable=True)         # list of {name, start_line, end_line}
    pos_x = Column(Float, nullable=True)            # saved canvas X position (Phase 5)
    pos_y = Column(Float, nullable=True)            # saved canvas Y position (Phase 5)

    snapshot = relationship("Snapshot", back_populates="file_nodes")

    # Outgoing edges (this file imports something)
    outgoing_edges = relationship(
        "DependencyEdge",
        foreign_keys="DependencyEdge.source_node_id",
        back_populates="source_node",
        cascade="all, delete-orphan",
    )
    # Incoming edges (this file is imported by something)
    incoming_edges = relationship(
        "DependencyEdge",
        foreign_keys="DependencyEdge.target_node_id",
        back_populates="target_node",
        cascade="all, delete-orphan",
    )


class DependencyEdge(Base):
    """
    Represents a resolved import dependency between two FileNodes.
    Only created when an import string can be mapped to a known file in the repo.
    Unresolved (third-party / stdlib) imports are stored in FileNode.imports but
    do NOT produce an edge here.
    """
    __tablename__ = "dependency_edges"

    id = Column(String, primary_key=True, default=generate_uuid)
    snapshot_id = Column(String, ForeignKey("snapshots.id", ondelete="CASCADE"), nullable=False)
    source_node_id = Column(String, ForeignKey("file_nodes.id", ondelete="CASCADE"), nullable=False)
    target_node_id = Column(String, ForeignKey("file_nodes.id", ondelete="CASCADE"), nullable=False)
    import_string = Column(String, nullable=False)   # raw import text that produced this edge
    edge_type = Column(String, nullable=False, default="import")  # "import" | "require"

    __table_args__ = (
        UniqueConstraint("snapshot_id", "source_node_id", "target_node_id", name="uq_edge_per_snapshot"),
    )

    snapshot = relationship("Snapshot", back_populates="dependency_edges")
    source_node = relationship("FileNode", foreign_keys=[source_node_id], back_populates="outgoing_edges")
    target_node = relationship("FileNode", foreign_keys=[target_node_id], back_populates="incoming_edges")


class AISummary(Base):
    __tablename__ = "ai_summaries"
    # Note: Not FK'd to file_nodes — this is a content-addressed cache (AD-005)

    id = Column(String, primary_key=True, default=generate_uuid)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String, nullable=False)
    content_hash = Column(String, nullable=False)  # cache key: same hash = same summary
    summary_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    __table_args__ = (
        UniqueConstraint("project_id", "file_path", "content_hash", name="uq_ai_summary_cache"),
    )