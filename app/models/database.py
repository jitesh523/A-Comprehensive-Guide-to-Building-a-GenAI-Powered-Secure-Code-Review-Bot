"""
Database models for persistence
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class ScanJob(Base):
    """Scan job tracking"""
    __tablename__ = "scan_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    repo_full_name = Column(String(255), nullable=False, index=True)
    pr_number = Column(Integer, nullable=True, index=True)
    commit_sha = Column(String(40), nullable=False)
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    findings = relationship("Finding", back_populates="scan_job", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ScanJob {self.repo_full_name} PR#{self.pr_number}>"


class Finding(Base):
    """Security finding from SAST + LLM verification"""
    __tablename__ = "findings"
    
    id = Column(Integer, primary_key=True, index=True)
    scan_job_id = Column(Integer, ForeignKey("scan_jobs.id"), nullable=False)
    
    # SAST metadata
    tool = Column(String(50), nullable=False)  # bandit, eslint, gosec, cargo-audit, cargo-clippy
    rule_id = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), nullable=False)
    description = Column(Text, nullable=False)
    file_path = Column(String(500), nullable=False)
    line_number = Column(Integer, nullable=False)
    code_snippet = Column(Text, nullable=True)
    
    # LLM verification
    llm_decision = Column(String(20), nullable=True)  # true_positive, false_positive, uncertain
    llm_confidence = Column(Float, nullable=True)
    llm_reasoning = Column(Text, nullable=True)
    llm_severity = Column(String(20), nullable=True)
    llm_remediation = Column(Text, nullable=True)
    cwe_ids = Column(JSON, nullable=True)
    
    # Status
    reported_to_pr = Column(Boolean, default=False)
    false_positive_marked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    scan_job = relationship("ScanJob", back_populates="findings")
    
    def __repr__(self):
        return f"<Finding {self.tool}:{self.rule_id} {self.llm_decision}>"


class CustomRule(Base):
    """Custom SAST rule configuration"""
    __tablename__ = "custom_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    language = Column(String(50), nullable=False, index=True)  # python, javascript, go, rust, typescript
    tool = Column(String(50), nullable=False, index=True)  # bandit, eslint, gosec, cargo-clippy
    rule_id = Column(String(100), nullable=False, index=True)
    enabled = Column(Boolean, default=True, index=True)
    severity_override = Column(String(20), nullable=True)  # Override default severity
    custom_message = Column(Text, nullable=True)  # Custom message to display
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<CustomRule {self.tool}:{self.rule_id} enabled={self.enabled}>"


class RuleConfiguration(Base):
    """Global rule configuration settings"""
    __tablename__ = "rule_configurations"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(JSON, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<RuleConfiguration {self.key}>"


class AuditLog(Base):
    """Audit log for tracking system actions"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    event_type = Column(String(50), nullable=False, index=True)  # scan_started, llm_verified, comment_posted
    repo_full_name = Column(String(255), nullable=True)
    pr_number = Column(Integer, nullable=True)
    details = Column(JSON, nullable=True)
    
    def __repr__(self):
        return f"<AuditLog {self.event_type} {self.timestamp}>"
