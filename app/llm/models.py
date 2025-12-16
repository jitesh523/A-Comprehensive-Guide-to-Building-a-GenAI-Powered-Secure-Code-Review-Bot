"""
Pydantic models for LLM structured outputs
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class VerificationDecision(str, Enum):
    """Verification decision enum"""
    TRUE_POSITIVE = "true_positive"
    FALSE_POSITIVE = "false_positive"
    UNCERTAIN = "uncertain"


class SeverityLevel(str, Enum):
    """Severity level enum"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class VerificationResult(BaseModel):
    """
    Structured output from LLM verification.
    
    This model enforces strict JSON schema for reliable parsing.
    """
    decision: VerificationDecision = Field(
        description="Whether the SAST finding is a true positive, false positive, or uncertain"
    )
    
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score between 0.0 and 1.0"
    )
    
    reasoning: str = Field(
        min_length=10,
        max_length=500,
        description="Explanation of the decision (10-500 characters)"
    )
    
    severity: Optional[SeverityLevel] = Field(
        default=None,
        description="Adjusted severity level if different from SAST finding"
    )
    
    exploitability: Optional[str] = Field(
        default=None,
        max_length=200,
        description="How the vulnerability could be exploited (if true positive)"
    )
    
    remediation: Optional[str] = Field(
        default=None,
        max_length=300,
        description="Suggested fix or remediation steps (if true positive)"
    )
    
    false_positive_reason: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Why this is a false positive (if applicable)"
    )
    
    cwe_ids: Optional[List[str]] = Field(
        default=None,
        description="Relevant CWE IDs (e.g., ['CWE-89', 'CWE-79'])"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "decision": "true_positive",
                "confidence": 0.95,
                "reasoning": "MD5 is used for password hashing, which is cryptographically weak and vulnerable to rainbow table attacks.",
                "severity": "high",
                "exploitability": "Attacker can use rainbow tables to crack password hashes",
                "remediation": "Replace MD5 with bcrypt, scrypt, or Argon2 for password hashing",
                "cwe_ids": ["CWE-327", "CWE-916"]
            }
        }


class VerificationRequest(BaseModel):
    """
    Request model for LLM verification.
    """
    sast_tool: str = Field(description="SAST tool name (bandit, eslint)")
    rule_id: str = Field(description="SAST rule ID")
    severity: str = Field(description="SAST severity")
    description: str = Field(description="SAST finding description")
    code_context: str = Field(description="Sanitized code context")
    function_name: Optional[str] = Field(default=None, description="Function name")
    class_name: Optional[str] = Field(default=None, description="Class name")
    file_path: str = Field(description="File path")
    line_number: int = Field(description="Line number")
