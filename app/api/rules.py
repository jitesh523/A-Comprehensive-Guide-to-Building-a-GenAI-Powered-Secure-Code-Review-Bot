"""
API endpoints for custom SAST rule management
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.models.database import CustomRule, RuleConfiguration
from app.models.db_session import get_db
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rules", tags=["rules"])


# Pydantic models for request/response
class CustomRuleCreate(BaseModel):
    name: str
    language: str  # python, javascript, typescript, go, rust
    tool: str  # bandit, eslint, gosec, cargo-clippy
    rule_id: str
    enabled: bool = True
    severity_override: Optional[str] = None
    custom_message: Optional[str] = None
    description: Optional[str] = None


class CustomRuleUpdate(BaseModel):
    name: Optional[str] = None
    enabled: Optional[bool] = None
    severity_override: Optional[str] = None
    custom_message: Optional[str] = None
    description: Optional[str] = None


class CustomRuleResponse(BaseModel):
    id: int
    name: str
    language: str
    tool: str
    rule_id: str
    enabled: bool
    severity_override: Optional[str]
    custom_message: Optional[str]
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


@router.get("/", response_model=List[CustomRuleResponse])
async def list_rules(
    language: Optional[str] = Query(None, description="Filter by language"),
    tool: Optional[str] = Query(None, description="Filter by tool"),
    enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """
    List all custom rules with optional filtering.
    
    Args:
        language: Filter by programming language
        tool: Filter by SAST tool
        enabled: Filter by enabled status
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        db: Database session
        
    Returns:
        List of custom rules
    """
    query = db.query(CustomRule)
    
    if language:
        query = query.filter(CustomRule.language == language)
    if tool:
        query = query.filter(CustomRule.tool == tool)
    if enabled is not None:
        query = query.filter(CustomRule.enabled == enabled)
    
    rules = query.offset(skip).limit(limit).all()
    logger.info(f"Retrieved {len(rules)} rules")
    return rules


@router.get("/{rule_id}", response_model=CustomRuleResponse)
async def get_rule(rule_id: int, db: Session = Depends(get_db)):
    """
    Get a single custom rule by ID.
    
    Args:
        rule_id: Rule ID
        db: Database session
        
    Returns:
        Custom rule details
    """
    rule = db.query(CustomRule).filter(CustomRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@router.post("/", response_model=CustomRuleResponse, status_code=201)
async def create_rule(rule: CustomRuleCreate, db: Session = Depends(get_db)):
    """
    Create a new custom rule.
    
    Args:
        rule: Rule details
        db: Database session
        
    Returns:
        Created rule
    """
    # Validate language and tool
    valid_languages = ["python", "javascript", "typescript", "go", "rust"]
    valid_tools = ["bandit", "eslint", "gosec", "cargo-clippy", "cargo-audit"]
    
    if rule.language not in valid_languages:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid language. Must be one of: {', '.join(valid_languages)}"
        )
    
    if rule.tool not in valid_tools:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid tool. Must be one of: {', '.join(valid_tools)}"
        )
    
    # Check for duplicate rule_id for same tool
    existing = db.query(CustomRule).filter(
        CustomRule.tool == rule.tool,
        CustomRule.rule_id == rule.rule_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Rule {rule.tool}:{rule.rule_id} already exists"
        )
    
    # Create new rule
    db_rule = CustomRule(**rule.model_dump())
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    
    logger.info(f"Created rule: {rule.name} ({rule.tool}:{rule.rule_id})")
    return db_rule


@router.put("/{rule_id}", response_model=CustomRuleResponse)
async def update_rule(
    rule_id: int,
    rule: CustomRuleUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing custom rule.
    
    Args:
        rule_id: Rule ID
        rule: Updated rule details
        db: Database session
        
    Returns:
        Updated rule
    """
    db_rule = db.query(CustomRule).filter(CustomRule.id == rule_id).first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    # Update fields
    update_data = rule.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_rule, field, value)
    
    db_rule.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_rule)
    
    logger.info(f"Updated rule {rule_id}")
    return db_rule


@router.delete("/{rule_id}", status_code=204)
async def delete_rule(rule_id: int, db: Session = Depends(get_db)):
    """
    Delete a custom rule.
    
    Args:
        rule_id: Rule ID
        db: Database session
    """
    db_rule = db.query(CustomRule).filter(CustomRule.id == rule_id).first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    db.delete(db_rule)
    db.commit()
    
    logger.info(f"Deleted rule {rule_id}")
    return None


@router.post("/import")
async def import_rules(
    rules: List[CustomRuleCreate],
    db: Session = Depends(get_db)
):
    """
    Import multiple rules from JSON.
    
    Args:
        rules: List of rules to import
        db: Database session
        
    Returns:
        Import summary
    """
    imported = 0
    failed = 0
    errors = []
    
    for rule_data in rules:
        try:
            # Check for duplicate
            existing = db.query(CustomRule).filter(
                CustomRule.tool == rule_data.tool,
                CustomRule.rule_id == rule_data.rule_id
            ).first()
            
            if existing:
                failed += 1
                errors.append(f"Rule {rule_data.tool}:{rule_data.rule_id} already exists")
                continue
            
            db_rule = CustomRule(**rule_data.model_dump())
            db.add(db_rule)
            imported += 1
        except Exception as e:
            failed += 1
            errors.append(str(e))
    
    db.commit()
    
    logger.info(f"Imported {imported} rules, {failed} failed")
    return {
        "imported": imported,
        "failed": failed,
        "errors": errors[:10]  # Limit error messages
    }


@router.get("/export")
async def export_rules(
    language: Optional[str] = Query(None),
    tool: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Export rules as JSON.
    
    Args:
        language: Filter by language
        tool: Filter by tool
        db: Database session
        
    Returns:
        List of rules in JSON format
    """
    query = db.query(CustomRule)
    
    if language:
        query = query.filter(CustomRule.language == language)
    if tool:
        query = query.filter(CustomRule.tool == tool)
    
    rules = query.all()
    
    # Convert to dict for JSON serialization
    rules_data = [
        {
            "name": r.name,
            "language": r.language,
            "tool": r.tool,
            "rule_id": r.rule_id,
            "enabled": r.enabled,
            "severity_override": r.severity_override,
            "custom_message": r.custom_message,
            "description": r.description
        }
        for r in rules
    ]
    
    logger.info(f"Exported {len(rules_data)} rules")
    return rules_data

