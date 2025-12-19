"""
API endpoints for user feedback on findings
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.models.database import FeedbackEntry, Finding
from app.models.db_session import get_db
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/feedback", tags=["feedback"])


# Pydantic models
class FeedbackCreate(BaseModel):
    finding_id: int
    feedback_type: str  # true_positive, false_positive, false_negative
    comment: Optional[str] = None
    user_github_username: Optional[str] = None


class FeedbackResponse(BaseModel):
    id: int
    finding_id: int
    feedback_type: str
    comment: Optional[str]
    user_github_username: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class FeedbackStats(BaseModel):
    total_feedback: int
    true_positives: int
    false_positives: int
    false_negatives: int
    false_positive_rate: float


@router.post("/", response_model=FeedbackResponse, status_code=201)
async def submit_feedback(
    feedback: FeedbackCreate,
    db: Session = Depends(get_db)
):
    """
    Submit feedback on a finding.
    
    Args:
        feedback: Feedback details
        db: Database session
        
    Returns:
        Created feedback entry
    """
    # Validate feedback type
    valid_types = ["true_positive", "false_positive", "false_negative"]
    if feedback.feedback_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid feedback_type. Must be one of: {', '.join(valid_types)}"
        )
    
    # Check if finding exists
    finding = db.query(Finding).filter(Finding.id == feedback.finding_id).first()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    
    # Create feedback entry
    db_feedback = FeedbackEntry(**feedback.model_dump())
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    
    logger.info(f"Submitted feedback for finding {feedback.finding_id}: {feedback.feedback_type}")
    return db_feedback


@router.get("/stats", response_model=FeedbackStats)
async def get_feedback_stats(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    language: Optional[str] = Query(None),
    tool: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get feedback statistics.
    
    Args:
        start_date: Start date for filtering
        end_date: End date for filtering
        language: Filter by language
        tool: Filter by tool
        db: Database session
        
    Returns:
        Feedback statistics
    """
    query = db.query(FeedbackEntry)
    
    # Apply filters
    if start_date:
        query = query.filter(FeedbackEntry.created_at >= start_date)
    if end_date:
        query = query.filter(FeedbackEntry.created_at <= end_date)
    
    # Join with Finding for language/tool filtering
    if language or tool:
        query = query.join(Finding)
        if language:
            # Note: Would need to add language field to Finding model
            pass
        if tool:
            query = query.filter(Finding.tool == tool)
    
    # Count by feedback type
    total = query.count()
    tp = query.filter(FeedbackEntry.feedback_type == "true_positive").count()
    fp = query.filter(FeedbackEntry.feedback_type == "false_positive").count()
    fn = query.filter(FeedbackEntry.feedback_type == "false_negative").count()
    
    # Calculate false positive rate
    fp_rate = fp / total if total > 0 else 0.0
    
    logger.info(f"Feedback stats: total={total}, TP={tp}, FP={fp}, FN={fn}")
    
    return FeedbackStats(
        total_feedback=total,
        true_positives=tp,
        false_positives=fp,
        false_negatives=fn,
        false_positive_rate=fp_rate
    )


@router.get("/recent", response_model=List[FeedbackResponse])
async def get_recent_feedback(
    limit: int = Query(10, ge=1, le=100),
    feedback_type: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get recent feedback entries.
    
    Args:
        limit: Maximum number of entries to return
        feedback_type: Filter by feedback type
        db: Database session
        
    Returns:
        List of recent feedback entries
    """
    query = db.query(FeedbackEntry).order_by(FeedbackEntry.created_at.desc())
    
    if feedback_type:
        query = query.filter(FeedbackEntry.feedback_type == feedback_type)
    
    feedback_entries = query.limit(limit).all()
    logger.info(f"Retrieved {len(feedback_entries)} recent feedback entries")
    return feedback_entries


@router.get("/by-rule/{rule_id}")
async def get_feedback_by_rule(
    rule_id: str,
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get feedback for a specific rule.
    
    Useful for identifying rules with high false positive rates.
    
    Args:
        rule_id: SAST rule ID
        limit: Maximum number of entries
        db: Database session
        
    Returns:
        Feedback entries for the rule
    """
    # Join with Finding to filter by rule_id
    feedback_entries = db.query(FeedbackEntry).join(Finding).filter(
        Finding.rule_id == rule_id
    ).order_by(FeedbackEntry.created_at.desc()).limit(limit).all()
    
    # Calculate stats for this rule
    total = db.query(FeedbackEntry).join(Finding).filter(Finding.rule_id == rule_id).count()
    fp_count = db.query(FeedbackEntry).join(Finding).filter(
        Finding.rule_id == rule_id,
        FeedbackEntry.feedback_type == "false_positive"
    ).count()
    
    fp_rate = fp_count / total if total > 0 else 0.0
    
    logger.info(f"Feedback for rule {rule_id}: {total} total, {fp_count} FP ({fp_rate:.2%})")
    
    return {
        "rule_id": rule_id,
        "total_feedback": total,
        "false_positives": fp_count,
        "false_positive_rate": fp_rate,
        "recent_feedback": [
            {
                "id": f.id,
                "finding_id": f.finding_id,
                "feedback_type": f.feedback_type,
                "comment": f.comment,
                "user_github_username": f.user_github_username,
                "created_at": f.created_at
            }
            for f in feedback_entries
        ]
    }

