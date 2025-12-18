"""
Rust Scanner Wrapper combining cargo-audit and cargo-clippy
"""
import subprocess
import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class RustScanner:
    def __init__(self, config_path: str = "configs/clippy.toml"):
        self.config_path = config_path

    async def scan(self, target_path: str) -> List[Dict[str, Any]]:
        """
        Runs cargo-audit and cargo-clippy on the target directory.
        
        Args:
            target_path: Path to the Rust project directory (containing Cargo.toml)
            
        Returns:
            List of normalized findings
        """
        findings = []
        
        # Run cargo-audit for security advisories
        audit_findings = await self._run_cargo_audit(target_path)
        findings.extend(audit_findings)
        
        # Run cargo-clippy for security lints
        clippy_findings = await self._run_cargo_clippy(target_path)
        findings.extend(clippy_findings)
        
        return findings

    async def _run_cargo_audit(self, target_path: str) -> List[Dict[str, Any]]:
        """Run cargo-audit to check for vulnerable dependencies"""
        command = [
            "cargo", "audit",
            "--json",
            "--file", f"{target_path}/Cargo.lock"
        ]

        try:
            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                check=False,
                cwd=target_path
            )
            
            if result.stdout:
                data = json.loads(result.stdout)
                vulnerabilities = data.get("vulnerabilities", {}).get("list", [])
                return self._normalize_audit_results(vulnerabilities)
            else:
                return []

        except json.JSONDecodeError:
            logger.error("Failed to parse cargo-audit JSON output.")
            return []
        except FileNotFoundError:
            logger.error("cargo-audit not found. Please install: cargo install cargo-audit")
            return []
        except Exception as e:
            logger.error(f"cargo-audit scan failed: {str(e)}")
            return []

    async def _run_cargo_clippy(self, target_path: str) -> List[Dict[str, Any]]:
        """Run cargo-clippy for security lints"""
        command = [
            "cargo", "clippy",
            "--message-format=json",
            "--",
            "-W", "clippy::all"
        ]

        try:
            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                check=False,
                cwd=target_path
            )
            
            # Clippy outputs one JSON object per line
            findings = []
            for line in result.stdout.splitlines():
                if line.strip():
                    try:
                        data = json.loads(line)
                        if data.get("reason") == "compiler-message":
                            message = data.get("message", {})
                            # Only include security-related lints
                            if self._is_security_lint(message):
                                findings.append(message)
                    except json.JSONDecodeError:
                        continue
            
            return self._normalize_clippy_results(findings)

        except FileNotFoundError:
            logger.error("cargo-clippy not found. Please install: rustup component add clippy")
            return []
        except Exception as e:
            logger.error(f"cargo-clippy scan failed: {str(e)}")
            return []

    def _is_security_lint(self, message: Dict[str, Any]) -> bool:
        """Check if clippy lint is security-related"""
        code = message.get("code", {}).get("code", "")
        security_lints = [
            "clippy::unwrap_used",
            "clippy::expect_used",
            "clippy::panic",
            "clippy::unimplemented",
            "clippy::todo",
            "clippy::unreachable",
            "clippy::mem_forget",
            "clippy::cast_ptr_alignment",
            "clippy::transmute_ptr_to_ptr"
        ]
        return any(lint in code for lint in security_lints)

    def _normalize_audit_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize cargo-audit format to our internal Finding format"""
        normalized = []
        for r in results:
            advisory = r.get("advisory", {})
            package = r.get("package", {})
            
            normalized.append({
                "tool": "cargo-audit",
                "severity": "HIGH",  # All vulnerabilities are high severity
                "confidence": "HIGH",
                "description": f"{advisory.get('title', 'Security vulnerability')} in {package.get('name', 'unknown')} {package.get('version', '')}",
                "file": "Cargo.lock",
                "line": 0,
                "code": advisory.get("description", ""),
                "rule_id": advisory.get("id", "")
            })
        return normalized

    def _normalize_clippy_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Normalize cargo-clippy format to our internal Finding format"""
        normalized = []
        for r in results:
            spans = r.get("spans", [])
            if not spans:
                continue
            
            primary_span = spans[0]
            code = r.get("code", {}).get("code", "")
            
            # Map clippy level to severity
            level = r.get("level", "warning")
            severity = "HIGH" if level == "error" else "MEDIUM"
            
            normalized.append({
                "tool": "cargo-clippy",
                "severity": severity,
                "confidence": "HIGH",
                "description": r.get("message", ""),
                "file": primary_span.get("file_name", ""),
                "line": primary_span.get("line_start", 0),
                "code": primary_span.get("text", [{}])[0].get("text", "") if primary_span.get("text") else "",
                "rule_id": code
            })
        return normalized
