"""
Gosec Scanner Wrapper for Go SAST
"""
import subprocess
import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class GosecScanner:
    def __init__(self, config_path: str = "configs/gosec.yaml"):
        self.config_path = config_path

    async def scan(self, target_path: str) -> List[Dict[str, Any]]:
        """
        Runs gosec on the target directory and returns a list of findings.
        
        Args:
            target_path: Path to the directory or file to scan
            
        Returns:
            List of normalized findings
        """
        command = [
            "gosec",
            "-fmt=json",
            "-conf", self.config_path,
            f"{target_path}/..."
        ]

        try:
            # Run gosec in a subprocess
            # Gosec returns exit code 1 if issues are found, so check=False
            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                check=False
            )
            
            if result.stderr and "Error" in result.stderr:
                logger.warning(f"Gosec stderr: {result.stderr}")

            # Parse JSON output
            if result.stdout:
                data = json.loads(result.stdout)
                return self._normalize_results(data.get("Issues", []))
            else:
                return []

        except json.JSONDecodeError:
            logger.error("Failed to parse Gosec JSON output.")
            return []
        except FileNotFoundError:
            logger.error("Gosec not found. Please install: go install github.com/securego/gosec/v2/cmd/gosec@latest")
            return []
        except Exception as e:
            logger.error(f"Gosec scan failed: {str(e)}")
            return []

    def _normalize_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Normalize Gosec format to our internal Finding format.
        
        Args:
            results: Raw Gosec results
            
        Returns:
            Normalized findings
        """
        normalized = []
        for r in results:
            # Map gosec severity to our format
            severity = r.get("severity", "MEDIUM").upper()
            
            # Extract line number from the first occurrence
            line = 0
            if "line" in r:
                line = int(r["line"])
            
            normalized.append({
                "tool": "gosec",
                "severity": severity,
                "confidence": r.get("confidence", "HIGH").upper(),
                "description": r.get("details", ""),
                "file": r.get("file", ""),
                "line": line,
                "code": r.get("code", ""),
                "rule_id": r.get("rule_id", "")
            })
        return normalized
