"""
TypeScript Scanner Wrapper using ESLint with TypeScript plugins
"""
import subprocess
import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class TypeScriptScanner:
    def __init__(self, config_path: str = "configs/eslint.typescript.config.mjs"):
        self.config_path = config_path

    async def scan(self, target_path: str) -> List[Dict[str, Any]]:
        """
        Runs ESLint with TypeScript parser on the target directory.
        
        Args:
            target_path: Path to the directory or file to scan
            
        Returns:
            List of normalized findings
        """
        command = [
            "npx", "eslint",
            target_path,
            "--format", "json",
            "--config", self.config_path,
            "--ext", ".ts,.tsx"
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
            logger.error(f"TypeScript ESLint scan failed: {str(e)}")
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
                
                # Only include security-related rules
                if not self._is_security_rule(msg.get("ruleId", "")):
                    continue
                    
                normalized.append({
                    "tool": "eslint-typescript",
                    "severity": self._map_severity(msg.get("severity")),
                    "confidence": "HIGH",  # Static analysis is deterministic
                    "description": msg.get("message"),
                    "file": file_path,
                    "line": msg.get("line"),
                    "code": msg.get("source", ""),
                    "rule_id": msg.get("ruleId")
                })
        return normalized

    def _is_security_rule(self, rule_id: str) -> bool:
        """Check if the rule is security-related"""
        security_prefixes = [
            "security/",
            "no-unsanitized/",
            "@typescript-eslint/no-unsafe-",
            "@typescript-eslint/no-explicit-any",
            "no-eval",
            "no-implied-eval"
        ]
        return any(rule_id.startswith(prefix) for prefix in security_prefixes)

    def _map_severity(self, severity: int) -> str:
        """
        Map ESLint severity to our internal format.
        
        Args:
            severity: ESLint severity (1 = Warn, 2 = Error)
            
        Returns:
            Severity string
        """
        return "HIGH" if severity == 2 else "MEDIUM"
