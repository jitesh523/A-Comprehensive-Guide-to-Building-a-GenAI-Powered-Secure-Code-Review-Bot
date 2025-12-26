"""
Software Composition Analysis (SCA) Scanner

Scans dependencies for known vulnerabilities using multiple tools:
- Python: pip-audit, safety
- JavaScript/Node: npm audit
- Go: govulncheck
- Rust: cargo-audit (already integrated)
- Java: OWASP Dependency Check
"""
import subprocess
import json
from pathlib import Path
from typing import Any
import logging

logger = logging.getLogger(__name__)


class SCAScanner:
    """Software Composition Analysis scanner for detecting vulnerable dependencies"""
    
    def __init__(self):
        self.name = "sca"
    
    def scan_project(self, project_path: str) -> list[dict[str, Any]]:
        """
        Scan project dependencies for vulnerabilities.
        
        Args:
            project_path: Path to project directory
            
        Returns:
            List of vulnerability findings
        """
        findings = []
        path = Path(project_path)
        
        # Detect project type and scan accordingly
        if (path / "requirements.txt").exists() or (path / "pyproject.toml").exists():
            findings.extend(self._scan_python(path))
        
        if (path / "package.json").exists():
            findings.extend(self._scan_javascript(path))
        
        if (path / "go.mod").exists():
            findings.extend(self._scan_go(path))
        
        if (path / "Cargo.toml").exists():
            findings.extend(self._scan_rust(path))
        
        if (path / "pom.xml").exists() or (path / "build.gradle").exists():
            findings.extend(self._scan_java(path))
        
        return findings
    
    def _scan_python(self, project_path: Path) -> list[dict[str, Any]]:
        """Scan Python dependencies using pip-audit"""
        findings = []
        
        try:
            # Run pip-audit
            result = subprocess.run(
                ["pip-audit", "--format", "json", "--requirement", "requirements.txt"],
                cwd=str(project_path),
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0 or result.stdout:
                data = json.loads(result.stdout) if result.stdout else {}
                vulnerabilities = data.get("vulnerabilities", [])
                
                for vuln in vulnerabilities:
                    findings.append({
                        "file": "requirements.txt",
                        "line": 1,
                        "severity": self._map_severity(vuln.get("severity", "MEDIUM")),
                        "rule_id": vuln.get("id", "UNKNOWN"),
                        "description": f"Vulnerable dependency: {vuln.get('name')} {vuln.get('version')}",
                        "cve": vuln.get("id"),
                        "package": vuln.get("name"),
                        "version": vuln.get("version"),
                        "fixed_version": vuln.get("fix_versions", [None])[0],
                        "tool": "pip-audit"
                    })
        
        except subprocess.TimeoutExpired:
            logger.warning("pip-audit timeout")
        except FileNotFoundError:
            logger.info("pip-audit not installed, skipping Python SCA")
        except Exception as e:
            logger.error(f"Python SCA failed: {str(e)}")
        
        return findings
    
    def _scan_javascript(self, project_path: Path) -> list[dict[str, Any]]:
        """Scan JavaScript dependencies using npm audit"""
        findings = []
        
        try:
            # Run npm audit
            result = subprocess.run(
                ["npm", "audit", "--json"],
                cwd=str(project_path),
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.stdout:
                data = json.loads(result.stdout)
                vulnerabilities = data.get("vulnerabilities", {})
                
                for pkg_name, vuln_data in vulnerabilities.items():
                    findings.append({
                        "file": "package.json",
                        "line": 1,
                        "severity": vuln_data.get("severity", "medium").upper(),
                        "rule_id": f"NPM-{vuln_data.get('via', [{}])[0].get('cve', 'UNKNOWN')}",
                        "description": f"Vulnerable dependency: {pkg_name}",
                        "cve": vuln_data.get("via", [{}])[0].get("cve"),
                        "package": pkg_name,
                        "version": vuln_data.get("range", "unknown"),
                        "fixed_version": vuln_data.get("fixAvailable", {}).get("version"),
                        "tool": "npm-audit"
                    })
        
        except subprocess.TimeoutExpired:
            logger.warning("npm audit timeout")
        except FileNotFoundError:
            logger.info("npm not installed, skipping JavaScript SCA")
        except Exception as e:
            logger.error(f"JavaScript SCA failed: {str(e)}")
        
        return findings
    
    def _scan_go(self, project_path: Path) -> list[dict[str, Any]]:
        """Scan Go dependencies using govulncheck"""
        findings = []
        
        try:
            # Run govulncheck
            result = subprocess.run(
                ["govulncheck", "-json", "./..."],
                cwd=str(project_path),
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        if data.get("finding"):
                            vuln = data["finding"]
                            findings.append({
                                "file": "go.mod",
                                "line": 1,
                                "severity": "HIGH",
                                "rule_id": vuln.get("osv", "UNKNOWN"),
                                "description": vuln.get("description", "Vulnerable Go dependency"),
                                "cve": vuln.get("osv"),
                                "package": vuln.get("module"),
                                "version": vuln.get("found"),
                                "fixed_version": vuln.get("fixed"),
                                "tool": "govulncheck"
                            })
                    except json.JSONDecodeError:
                        continue
        
        except subprocess.TimeoutExpired:
            logger.warning("govulncheck timeout")
        except FileNotFoundError:
            logger.info("govulncheck not installed, skipping Go SCA")
        except Exception as e:
            logger.error(f"Go SCA failed: {str(e)}")
        
        return findings
    
    def _scan_rust(self, project_path: Path) -> list[dict[str, Any]]:
        """Scan Rust dependencies using cargo-audit"""
        findings = []
        
        try:
            # Run cargo audit
            result = subprocess.run(
                ["cargo", "audit", "--json"],
                cwd=str(project_path),
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.stdout:
                data = json.loads(result.stdout)
                vulnerabilities = data.get("vulnerabilities", {}).get("list", [])
                
                for vuln in vulnerabilities:
                    advisory = vuln.get("advisory", {})
                    findings.append({
                        "file": "Cargo.toml",
                        "line": 1,
                        "severity": "HIGH",
                        "rule_id": advisory.get("id", "UNKNOWN"),
                        "description": advisory.get("title", "Vulnerable Rust dependency"),
                        "cve": advisory.get("id"),
                        "package": vuln.get("package", {}).get("name"),
                        "version": vuln.get("package", {}).get("version"),
                        "fixed_version": advisory.get("patched_versions", [None])[0],
                        "tool": "cargo-audit"
                    })
        
        except subprocess.TimeoutExpired:
            logger.warning("cargo audit timeout")
        except FileNotFoundError:
            logger.info("cargo not installed, skipping Rust SCA")
        except Exception as e:
            logger.error(f"Rust SCA failed: {str(e)}")
        
        return findings
    
    def _scan_java(self, project_path: Path) -> list[dict[str, Any]]:
        """Scan Java dependencies using OWASP Dependency Check"""
        findings = []
        
        try:
            # Run dependency-check
            result = subprocess.run(
                [
                    "dependency-check",
                    "--project", "scan",
                    "--scan", str(project_path),
                    "--format", "JSON",
                    "--out", "/tmp/dependency-check-report.json"
                ],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            report_path = Path("/tmp/dependency-check-report.json")
            if report_path.exists():
                with open(report_path) as f:
                    data = json.load(f)
                
                dependencies = data.get("dependencies", [])
                for dep in dependencies:
                    vulnerabilities = dep.get("vulnerabilities", [])
                    for vuln in vulnerabilities:
                        findings.append({
                            "file": "pom.xml",
                            "line": 1,
                            "severity": vuln.get("severity", "MEDIUM"),
                            "rule_id": vuln.get("name", "UNKNOWN"),
                            "description": vuln.get("description", "Vulnerable Java dependency"),
                            "cve": vuln.get("name"),
                            "package": dep.get("fileName"),
                            "version": "unknown",
                            "fixed_version": None,
                            "tool": "dependency-check"
                        })
                
                report_path.unlink()
        
        except subprocess.TimeoutExpired:
            logger.warning("dependency-check timeout")
        except FileNotFoundError:
            logger.info("dependency-check not installed, skipping Java SCA")
        except Exception as e:
            logger.error(f"Java SCA failed: {str(e)}")
        
        return findings
    
    def _map_severity(self, severity: str) -> str:
        """Map various severity formats to standard levels"""
        severity_upper = severity.upper()
        
        if severity_upper in ["CRITICAL", "HIGH"]:
            return "HIGH"
        elif severity_upper in ["MEDIUM", "MODERATE"]:
            return "MEDIUM"
        elif severity_upper in ["LOW", "INFO"]:
            return "LOW"
        else:
            return "MEDIUM"


def scan_dependencies(project_path: str) -> list[dict[str, Any]]:
    """
    Convenience function to scan project dependencies.
    
    Args:
        project_path: Path to project directory
        
    Returns:
        List of vulnerability findings
    """
    scanner = SCAScanner()
    return scanner.scan_project(project_path)
