"""
Celery task orchestrator for scan workflows
"""
from app.celery_app import celery_app
from app.scanners.scanner_with_context import ScannerWithContext
from app.privacy.sanitizer import PrivacySanitizer
from app.llm.verifier import LLMVerifier
from app.git.github_client import GitHubClient
from app.config import settings
import logging
import os
import shutil

logger = logging.getLogger(__name__)


@celery_app.task(name="process_pull_request")
def process_pull_request(repo_full_name: str, pr_number: int, head_sha: str):
    """
    Process a pull request: scan, verify, and comment.
    
    Args:
        repo_full_name: Full repository name (owner/repo)
        pr_number: Pull request number
        head_sha: Commit SHA
    """
    logger.info(f"Processing PR #{pr_number} in {repo_full_name}")
    
    try:
        # Initialize components
        github_client = GitHubClient()
        scanner = ScannerWithContext()
        sanitizer = PrivacySanitizer()
        verifier = LLMVerifier()
        
        # Clone repository
        clone_dir = f"/app/cloned_repos/{repo_full_name.replace('/', '_')}_{pr_number}"
        os.makedirs(clone_dir, exist_ok=True)
        
        logger.info(f"Cloning repository to {clone_dir}")
        if not github_client.clone_repository(repo_full_name, clone_dir):
            logger.error("Failed to clone repository")
            return
        
        # Get PR files
        pr_files = github_client.get_pr_files(repo_full_name, pr_number)
        logger.info(f"PR has {len(pr_files)} changed files")
        
        # Scan repository
        logger.info("Running SAST scans...")
        import asyncio
        results = asyncio.run(scanner.scan_repository(clone_dir))
        
        all_findings = results.get('python', []) + results.get('javascript', [])
        logger.info(f"Found {len(all_findings)} total findings")
        
        # Filter findings to only PR-changed files
        pr_findings = [
            f for f in all_findings
            if any(pr_file in f.get('file', '') for pr_file in pr_files)
        ]
        logger.info(f"Filtered to {len(pr_findings)} findings in PR files")
        
        # Process each finding
        verified_findings = []
        for finding in pr_findings[:10]:  # Limit to first 10 for cost control
            # Sanitize
            sanitized_finding, _ = sanitizer.sanitize_finding(finding)
            
            # Verify with LLM
            verification = asyncio.run(verifier.verify_finding(sanitized_finding))
            
            # Only report true positives
            if verification.decision.value == "true_positive":
                verified_findings.append((finding, verification))
        
        logger.info(f"Verified {len(verified_findings)} true positives")
        
        # Post comments
        if verified_findings:
            # Post summary comment
            summary = f"🔒 **Security Scan Complete**\n\n"
            summary += f"Found **{len(verified_findings)} verified security issues** in this PR.\n\n"
            summary += "See inline comments for details."
            
            github_client.post_pr_comment(repo_full_name, pr_number, summary)
            
            # Post inline comments
            for finding, verification in verified_findings:
                comment = github_client.format_finding_comment(finding, verification)
                
                # Try to post as review comment (inline)
                # Note: This requires the file to be in the PR diff
                file_path = finding.get('file', '').replace(clone_dir + '/', '')
                success = github_client.post_review_comment(
                    repo_full_name=repo_full_name,
                    pr_number=pr_number,
                    commit_id=head_sha,
                    file_path=file_path,
                    line=finding.get('line', 1),
                    body=comment
                )
                
                if not success:
                    # Fallback: post as general comment
                    github_client.post_pr_comment(
                        repo_full_name,
                        pr_number,
                        f"**{file_path}:{finding.get('line')}**\n\n{comment}"
                    )
        else:
            # No issues found
            github_client.post_pr_comment(
                repo_full_name,
                pr_number,
                "✅ **Security Scan Complete** - No verified security issues found!"
            )
        
        # Cleanup
        shutil.rmtree(clone_dir, ignore_errors=True)
        logger.info("Scan complete")
        
    except Exception as e:
        logger.error(f"Error processing PR: {str(e)}")
        import traceback
        traceback.print_exc()


@celery_app.task(name="process_push")
def process_push(repo_full_name: str, head_sha: str):
    """
    Process a push event (future enhancement).
    
    Args:
        repo_full_name: Full repository name (owner/repo)
        head_sha: Commit SHA
    """
    logger.info(f"Processing push to {repo_full_name} ({head_sha})")
    # TODO: Implement push scanning
    pass
