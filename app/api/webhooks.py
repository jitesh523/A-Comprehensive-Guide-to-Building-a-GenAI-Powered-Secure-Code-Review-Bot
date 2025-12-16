"""
GitHub webhook endpoint and handlers
"""
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from app.config import settings
from typing import Dict, Any
import hmac
import hashlib
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["webhooks"])


def verify_github_signature(payload: bytes, signature: str) -> bool:
    """
    Verify GitHub webhook signature using HMAC-SHA256.
    
    Args:
        payload: Raw request body
        signature: X-Hub-Signature-256 header value
        
    Returns:
        True if signature is valid
    """
    if not settings.GITHUB_WEBHOOK_SECRET:
        logger.warning("GitHub webhook secret not configured - skipping validation")
        return True
    
    if not signature:
        logger.error("No signature provided")
        return False
    
    # Extract signature (format: "sha256=...")
    if not signature.startswith("sha256="):
        logger.error("Invalid signature format")
        return False
    
    expected_signature = signature.split("=")[1]
    
    # Compute HMAC
    secret = settings.GITHUB_WEBHOOK_SECRET.encode()
    computed_hmac = hmac.new(secret, payload, hashlib.sha256).hexdigest()
    
    # Constant-time comparison
    return hmac.compare_digest(computed_hmac, expected_signature)


@router.post("/github")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Handle GitHub webhook events.
    
    Supported events:
    - pull_request (opened, synchronize)
    - push
    """
    # Get signature
    signature = request.headers.get("X-Hub-Signature-256")
    
    # Read raw body
    body = await request.body()
    
    # Verify signature
    if not verify_github_signature(body, signature):
        logger.error("Invalid webhook signature")
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Parse JSON
    payload = await request.json()
    
    # Get event type
    event_type = request.headers.get("X-GitHub-Event")
    
    logger.info(f"Received GitHub webhook: {event_type}")
    
    # Handle different event types
    if event_type == "pull_request":
        return await handle_pull_request(payload, background_tasks)
    elif event_type == "push":
        return await handle_push(payload, background_tasks)
    elif event_type == "ping":
        return {"message": "pong"}
    else:
        logger.warning(f"Unsupported event type: {event_type}")
        return {"message": f"Event {event_type} not handled"}


async def handle_pull_request(payload: Dict[str, Any], background_tasks: BackgroundTasks):
    """
    Handle pull_request webhook event.
    
    Args:
        payload: Webhook payload
        background_tasks: FastAPI background tasks
        
    Returns:
        Response dict
    """
    action = payload.get("action")
    
    # Only process opened and synchronize (new commits)
    if action not in ["opened", "synchronize"]:
        logger.info(f"Ignoring PR action: {action}")
        return {"message": f"PR action {action} ignored"}
    
    pr = payload.get("pull_request", {})
    repo = payload.get("repository", {})
    
    pr_number = pr.get("number")
    repo_full_name = repo.get("full_name")
    head_sha = pr.get("head", {}).get("sha")
    
    logger.info(f"Processing PR #{pr_number} in {repo_full_name}")
    
    # Queue scan job in background
    from app.tasks.scan_orchestrator import process_pull_request
    background_tasks.add_task(
        process_pull_request,
        repo_full_name=repo_full_name,
        pr_number=pr_number,
        head_sha=head_sha
    )
    
    return {
        "message": "Scan queued",
        "pr_number": pr_number,
        "repo": repo_full_name
    }


async def handle_push(payload: Dict[str, Any], background_tasks: BackgroundTasks):
    """
    Handle push webhook event.
    
    Args:
        payload: Webhook payload
        background_tasks: FastAPI background tasks
        
    Returns:
        Response dict
    """
    repo = payload.get("repository", {})
    ref = payload.get("ref")
    
    # Only process main/master branch
    if ref not in ["refs/heads/main", "refs/heads/master"]:
        logger.info(f"Ignoring push to {ref}")
        return {"message": f"Push to {ref} ignored"}
    
    repo_full_name = repo.get("full_name")
    head_sha = payload.get("after")
    
    logger.info(f"Processing push to {repo_full_name}")
    
    # Queue scan job in background
    from app.tasks.scan_orchestrator import process_push
    background_tasks.add_task(
        process_push,
        repo_full_name=repo_full_name,
        head_sha=head_sha
    )
    
    return {
        "message": "Scan queued",
        "repo": repo_full_name,
        "sha": head_sha
    }
