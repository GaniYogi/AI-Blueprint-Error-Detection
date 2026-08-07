import datetime
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Float, Text
from sqlalchemy.orm import relationship
from app.db.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    blueprints = relationship("Blueprint", back_populates="owner", cascade="all, delete-orphan")

class Blueprint(Base):
    __tablename__ = "blueprints"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    original_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    content_type = Column(String, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status = Column(String, default="pending")  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    owner = relationship("User", back_populates="blueprints")
    analysis_results = relationship("AnalysisResult", back_populates="blueprint", uselist=False, cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="blueprint", cascade="all, delete-orphan")

class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)
    blueprint_id = Column(Integer, ForeignKey("blueprints.id", ondelete="CASCADE"), unique=True, nullable=False)
    compliance_score = Column(Float, default=100.0)
    total_errors = Column(Integer, default=0)
    total_violations = Column(Integer, default=0)
    raw_json = Column(Text, nullable=False)  # Stores serialized dict with detected_objects, errors, compliance_checks, ocr_results
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    blueprint = relationship("Blueprint", back_populates="analysis_results")

class ComplianceRule(Base):
    __tablename__ = "compliance_rules"

    id = Column(Integer, primary_key=True, index=True)
    rule_key = Column(String, unique=True, index=True, nullable=False)  # e.g., "min_bedroom_area"
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String, nullable=False)  # e.g., "space", "ventilation", "accessibility"
    default_value = Column(Float, nullable=False)
    current_value = Column(Float, nullable=False)
    unit = Column(String, nullable=False)  # e.g., "sq ft", "ft", "%"
    severity = Column(String, default="Medium")  # Low, Medium, High, Critical
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    blueprint_id = Column(Integer, ForeignKey("blueprints.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    blueprint = relationship("Blueprint", back_populates="reports")
