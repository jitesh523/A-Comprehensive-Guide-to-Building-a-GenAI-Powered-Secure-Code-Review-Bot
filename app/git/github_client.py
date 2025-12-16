"""
GitHub API client for repository operations and PR comments
"""
from github import Github, GithubException
from app.config import settings
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class GitHubClient:
    """
    GitHub API client for interacting with repositories and PRs.
    """
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize GitHub client.
        
        Args:
            token: GitHub personal access token (defaults to settings.GITHUB_TOKEN)
        """
        self.token = token or settings.GITHUB_TOKEN
        if not self.token:
            raise ValueError("GitHub token not configured")
        
        self.client = Github(self.token)
        logger.info("Initialized GitHub client")
    
    def get_repository(self, repo_full_name: str):
        """
        Get repository object.
        
        Args:
            repo_full_name: Full repository name (owner/repo)
            
        Returns:
            Repository object
        """
        try:
            return self.client.get_repo(repo_full_name)
        except GithubException as e:
            logger.error(f"Failed to get repository {repo_full_name}: {str(e)}")
            raise
    
    def get_pull_request(self, repo_full_name: str, pr_number: int):
        """
        Get pull request object.
        
        Args:
            repo_full_name: Full repository name (owner/repo)
            pr_number: Pull request number
            
        Returns:
            PullRequest object
        """
        try:
            repo = self.get_repository(repo_full_name)
            return repo.get_pull(pr_number)
        except GithubException as e:
            logger.error(f"Failed to get PR #{pr_number}: {str(e)}")
            raise
    
    def post_pr_comment(
        self,
        repo_full_name: str,
        pr_number: int,
        body: str
    ) -> bool:
        """
        Post a comment on a pull request.
        
        Args:
            repo_full_name: Full repository name (owner/repo)
            pr_number: Pull request number
            body: Comment body (markdown supported)
            
        Returns:
            True if successful
        """
        try:
            pr = self.get_pull_request(repo_full_name, pr_number)
            pr.create_issue_comment(body)
            logger.info(f"Posted comment to PR #{pr_number}")
            return True
        except GithubException as e:
            logger.error(f"Failed to post comment: {str(e)}")
            return False
    
    def post_review_comment(
        self,
        repo_full_name: str,
        pr_number: int,
        commit_id: str,
        file_path: str,
        line: int,
        body: str
    ) -> bool:
        """
        Post an inline review comment on a specific line.
        
        Args:
            repo_full_name: Full repository name (owner/repo)
            pr_number: Pull request number
            commit_id: Commit SHA
            file_path: File path relative to repo root
            line: Line number
            body: Comment body
            
        Returns:
            True if successful
        """
        try:
            pr = self.get_pull_request(repo_full_name, pr_number)
            pr.create_review_comment(
                body=body,
                commit_id=commit_id,
                path=file_path,
                line=line
            )
            logger.info(f"Posted review comment at {file_path}:{line}")
            return True
        except GithubException as e:
            logger.error(f"Failed to post review comment: {str(e)}")
            return False
    
    def get_pr_files(self, repo_full_name: str, pr_number: int) -> List[str]:
        """
        Get list of files changed in a PR.
        
        Args:
            repo_full_name: Full repository name (owner/repo)
            pr_number: Pull request number
            
        Returns:
            List of file paths
        """
        try:
            pr = self.get_pull_request(repo_full_name, pr_number)
            files = pr.get_files()
            return [f.filename for f in files]
        except GithubException as e:
            logger.error(f"Failed to get PR files: {str(e)}")
            return []
    
    def clone_repository(
        self,
        repo_full_name: str,
        target_dir: str,
        branch: Optional[str] = None
    ) -> bool:
        """
        Clone a repository to local directory.
        
        Args:
            repo_full_name: Full repository name (owner/repo)
            target_dir: Target directory for clone
            branch: Branch to clone (optional)
            
        Returns:
            True if successful
        """
        try:
            import git
            
            repo_url = f"https://{self.token}@github.com/{repo_full_name}.git"
            
            if branch:
                git.Repo.clone_from(repo_url, target_dir, branch=branch)
            else:
                git.Repo.clone_from(repo_url, target_dir)
            
            logger.info(f"Cloned {repo_full_name} to {target_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clone repository: {str(e)}")
            return False
    
    def format_finding_comment(self, finding: Dict[str, Any], verification: Any) -> str:
        """
        Format a finding and verification result as a markdown comment.
        
        Args:
            finding: Finding dictionary
            verification: VerificationResult object
            
        Returns:
            Formatted markdown comment
        """
        # Determine emoji based on decision
        emoji_map = {
            "true_positive": "🚨",
            "false_positive": "✅",
            "uncertain": "⚠️"
        }
        emoji = emoji_map.get(verification.decision.value, "ℹ️")
        
        # Build comment
        lines = [
            f"{emoji} **Security Finding: {finding.get('rule_id')}**",
            "",
            f"**Decision**: {verification.decision.value.replace('_', ' ').title()}",
            f"**Confidence**: {verification.confidence:.0%}",
            f"**Severity**: {verification.severity.value if verification.severity else finding.get('severity')}",
            "",
            f"**Reasoning**: {verification.reasoning}",
        ]
        
        if verification.exploitability:
            lines.extend([
                "",
                f"**Exploitability**: {verification.exploitability}"
            ])
        
        if verification.remediation:
            lines.extend([
                "",
                f"**Remediation**: {verification.remediation}"
            ])
        
        if verification.cwe_ids:
            cwe_links = [
                f"[{cwe}](https://cwe.mitre.org/data/definitions/{cwe.replace('CWE-', '')}.html)"
                for cwe in verification.cwe_ids
            ]
            lines.extend([
                "",
                f"**CWE**: {', '.join(cwe_links)}"
            ])
        
        lines.extend([
            "",
            "---",
            f"*Analyzed by Secure Code Review Bot*"
        ])
        
        return "\n".join(lines)
