"""
Bandit Scanner Wrapper for Python SAST
"""
import subprocess
import json
import logging
from typing import List, Dict, Any

# Configure logging
logger = logging.getLogger(__name__)


class BanditScanner:
    def __init__(self, config_path: str = "configs/bandit.yaml"):
        self.config_path = config_path

    async def scan(self, target_path: str) -> List[Dict[str, Any]]:
        """
        Runs Bandit on the target directory and returns a list of findings.
        
        Args:
            target_path: Path to the directory or file to scan
            
        Returns:
            List of normalized findings
        """
        command = [
            "bandit",
            "-r", target_path,
            "-f", "json",
            "-c", self.config_path
        ]

        try:
            # Run bandit in a subprocess
            # Bandit returns exit code 1 if issues are found, so check=False
            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                check=False
            )
            
            if result.stderr:
                logger.warning(f"Bandit stderr: {result.stderr}")

            # Parse JSON output
            data = json.loads(result.stdout)
            return self._normalize_results(data.get("results", []))

        except json.JSONDecodeError:
            logger.error("Failed to parse Bandit JSON output.")
            return []
        except Exception as e:
            logger.error(f"Bandit scan failed: {str(e)}")
            return []

    def _normalize_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize Bandit format to our internal Finding format.
        
        Args:
            results: Raw Bandit results
            
        Returns:
            Normalized findings
        """
        normalized = []
        for r in results:
            normalized.append({
                "tool": "bandit",
                "severity": r.get("issue_severity"),
                "confidence": r.get("issue_confidence"),
                "description": r.get("issue_text"),
                "file": r.get("filename"),
                "line": r.get("line_number"),
                "code": r.get("code"),  # The snippet provided by bandit
                "rule_id": r.get("test_id")
            })
        return normalized
