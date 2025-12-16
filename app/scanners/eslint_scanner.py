"""
ESLint Scanner Wrapper for JavaScript SAST
"""
import subprocess
import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class ESLintScanner:
    def __init__(self, config_path: str = "configs/eslint.config.mjs"):
        self.config_path = config_path

    async def scan(self, target_path: str) -> List[Dict[str, Any]]:
        """
        Runs ESLint on the target directory.
        
        Args:
            target_path: Path to the directory or file to scan
            
        Returns:
            List of normalized findings
        """
        command = [
            "npx", "eslint",
            target_path,
            "--format", "json",
            "--config", self.config_path
        ]

        try:
            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                check=False
            )
            
            # ESLint outputs JSON to stdout
            try:
                data = json.loads(result.stdout)
                return self._normalize_results(data)
            except json.JSONDecodeError:
                # If output is empty or not JSON (common if no files found)
                if result.stderr:
                    logger.warning(f"ESLint stderr: {result.stderr}")
                return []

        except Exception as e:
            logger.error(f"ESLint scan failed: {str(e)}")
            return []

    def _normalize_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize ESLint format to our internal Finding format.
        
        Args:
            results: Raw ESLint results
            
        Returns:
            Normalized findings
        """
        normalized = []
        for file_result in results:
            file_path = file_result.get("filePath", "")
            
            for msg in file_result.get("messages", []):
                # We filter out stylistic issues (if any slipped through)
                if not msg.get("ruleId"): 
                    continue
                    
                normalized.append({
                    "tool": "eslint",
                    "severity": self._map_severity(msg.get("severity")),
                    "confidence": "High",  # Static analysis is deterministic
                    "description": msg.get("message"),
                    "file": file_path,
                    "line": msg.get("line"),
                    "code": msg.get("source", ""),  # ESLint often doesn't return source in JSON
                    "rule_id": msg.get("ruleId")
                })
        return normalized

    def _map_severity(self, severity: int) -> str:
        """
        Map ESLint severity to our internal format.
        
        Args:
            severity: ESLint severity (1 = Warn, 2 = Error)
            
        Returns:
            Severity string
        """
        return "HIGH" if severity == 2 else "MEDIUM"
