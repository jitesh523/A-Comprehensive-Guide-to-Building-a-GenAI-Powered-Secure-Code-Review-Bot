"""
Incremental scanner - only scan changed files
"""
import os
import hashlib
import subprocess
from pathlib import Path
from typing import List, Dict, Set, Optional
import logging

logger = logging.getLogger(__name__)


class IncrementalScanner:
    """Track file changes and scan only modified files"""
    
    def __init__(self, repo_path: str):
        """
        Initialize incremental scanner.
        
        Args:
            repo_path: Path to Git repository
        """
        self.repo_path = Path(repo_path)
        self.is_git_repo = self._check_git_repo()
    
    def _check_git_repo(self) -> bool:
        """Check if path is a Git repository"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--git-dir"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception as e:
            logger.warning(f"Not a Git repository: {str(e)}")
            return False
    
    def get_changed_files(
        self,
        base_ref: str = "HEAD~1",
        extensions: Optional[Set[str]] = None
    ) -> List[str]:
        """
        Get list of changed files since base reference.
        
        Args:
            base_ref: Git reference to compare against (default: HEAD~1)
            extensions: Set of file extensions to include (e.g., {'.py', '.js'})
            
        Returns:
            List of changed file paths
        """
        if not self.is_git_repo:
            logger.warning("Not a Git repo, scanning all files")
            return self._get_all_files(extensions)
        
        try:
            # Get changed files using git diff
            result = subprocess.run(
                ["git", "diff", "--name-only", base_ref, "HEAD"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                logger.error(f"Git diff failed: {result.stderr}")
                return self._get_all_files(extensions)
            
            files = result.stdout.strip().split('\n')
            files = [f for f in files if f]  # Remove empty strings
            
            # Filter by extensions if specified
            if extensions:
                files = [
                    f for f in files
                    if any(f.endswith(ext) for ext in extensions)
                ]
            
            # Convert to absolute paths
            files = [str(self.repo_path / f) for f in files]
            
            # Filter out deleted files
            files = [f for f in files if os.path.exists(f)]
            
            logger.info(f"Found {len(files)} changed files")
            return files
            
        except Exception as e:
            logger.error(f"Failed to get changed files: {str(e)}")
            return self._get_all_files(extensions)
    
    def _get_all_files(self, extensions: Optional[Set[str]] = None) -> List[str]:
        """
        Get all files in repository (fallback).
        
        Args:
            extensions: Set of file extensions to include
            
        Returns:
            List of all file paths
        """
        files = []
        
        for root, _, filenames in os.walk(self.repo_path):
            # Skip common ignore patterns
            if any(ignore in root for ignore in ['.git', 'node_modules', '__pycache__', '.venv', 'venv']):
                continue
            
            for filename in filenames:
                if extensions and not any(filename.endswith(ext) for ext in extensions):
                    continue
                
                file_path = os.path.join(root, filename)
                files.append(file_path)
        
        logger.info(f"Found {len(files)} total files")
        return files
    
    def compute_file_hash(self, file_path: str) -> str:
        """
        Compute SHA256 hash of file content.
        
        Args:
            file_path: Path to file
            
        Returns:
            SHA256 hash as hex string
        """
        try:
            with open(file_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            return file_hash
        except Exception as e:
            logger.error(f"Failed to hash file {file_path}: {str(e)}")
            return ""
    
    def get_files_by_language(
        self,
        language: str,
        only_changed: bool = True,
        base_ref: str = "HEAD~1"
    ) -> List[Dict[str, str]]:
        """
        Get files for a specific language.
        
        Args:
            language: Programming language
            only_changed: If True, only return changed files
            base_ref: Git reference for comparison
            
        Returns:
            List of dicts with 'path' and 'hash' keys
        """
        # Map language to file extensions
        extension_map = {
            "python": {".py"},
            "javascript": {".js", ".jsx"},
            "typescript": {".ts", ".tsx"},
            "go": {".go"},
            "rust": {".rs"}
        }
        
        extensions = extension_map.get(language.lower())
        if not extensions:
            logger.warning(f"Unknown language: {language}")
            return []
        
        # Get files
        if only_changed:
            files = self.get_changed_files(base_ref, extensions)
        else:
            files = self._get_all_files(extensions)
        
        # Compute hashes
        result = []
        for file_path in files:
            file_hash = self.compute_file_hash(file_path)
            if file_hash:
                result.append({
                    "path": file_path,
                    "hash": file_hash
                })
        
        return result
    
    def should_scan_file(
        self,
        file_path: str,
        cached_hash: Optional[str] = None
    ) -> bool:
        """
        Determine if file should be scanned.
        
        Args:
            file_path: Path to file
            cached_hash: Previously cached file hash
            
        Returns:
            True if file should be scanned
        """
        if not os.path.exists(file_path):
            return False
        
        if cached_hash is None:
            return True
        
        current_hash = self.compute_file_hash(file_path)
        return current_hash != cached_hash
