"""
C/C++ Security Scanner using Cppcheck and Clang-Tidy

This scanner integrates Cppcheck for static analysis and can optionally
use Clang-Tidy for additional modern C++ checks.
"""
import subprocess
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


class CppScanner:
    """
    C/C++ security scanner using Cppcheck.
    """
    
    def __init__(self):
        self.name = "cppcheck"
        self.language = "cpp"
    
    def scan(self, file_path: str) -> list[dict[str, Any]]:
        """
        Scan a C/C++ file or project for security vulnerabilities.
        
        Args:
            file_path: Path to C/C++ file or project directory
            
        Returns:
            List of security findings
        """
        findings = []
        path = Path(file_path)
        
        # Run Cppcheck
        findings.extend(self._run_cppcheck(path))
        
        # Optionally run Clang-Tidy if available
        try:
            subprocess.run(["clang-tidy", "--version"], capture_output=True, check=True)
            findings.extend(self._run_clang_tidy(path))
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Clang-Tidy not available, skip
            pass
        
        return findings
    
    def _run_cppcheck(self, path: Path) -> list[dict[str, Any]]:
        """
        Run Cppcheck on C/C++ code.
        
        Args:
            path: Path to file or directory
            
        Returns:
            List of security findings
        """
        findings = []
        
        try:
            # Create temporary output file
            output_file = Path("/tmp/cppcheck-output.xml")
            
            # Run Cppcheck with security-focused checks
            cmd = [
                "cppcheck",
                "--enable=all",  # Enable all checks
                "--xml",  # XML output
                "--xml-version=2",
                f"--output-file={output_file}",
                "--suppress=missingIncludeSystem",  # Suppress missing system includes
                "--suppress=unmatchedSuppression",
                "--inline-suppr",
                "--force",  # Force checking all configurations
                str(path)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            # Parse XML output
            if output_file.exists():
                findings = self._parse_cppcheck_xml(output_file)
                output_file.unlink()
        
        except subprocess.TimeoutExpired:
            findings = [{
                "file": str(path),
                "line": 1,
                "severity": "ERROR",
                "rule_id": "TIMEOUT",
                "description": "Cppcheck scan timeout exceeded",
                "tool": "cppcheck"
            }]
        except Exception as e:
            findings = [{
                "file": str(path),
                "line": 1,
                "severity": "ERROR",
                "rule_id": "SCAN_ERROR",
                "description": f"Cppcheck scan error: {str(e)}",
                "tool": "cppcheck"
            }]
        
        return findings
    
    def _parse_cppcheck_xml(self, xml_file: Path) -> list[dict[str, Any]]:
        """
        Parse Cppcheck XML output.
        
        Args:
            xml_file: Path to Cppcheck XML output file
            
        Returns:
            List of security findings
        """
        findings = []
        
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            # Parse error elements
            for error in root.findall(".//error"):
                # Get error details
                error_id = error.get("id", "UNKNOWN")
                severity = error.get("severity", "style")
                msg = error.get("msg", "No description")
                verbose = error.get("verbose", msg)
                
                # Map Cppcheck severity to our severity levels
                severity_map = {
                    "error": "HIGH",
                    "warning": "MEDIUM",
                    "style": "LOW",
                    "performance": "LOW",
                    "portability": "LOW",
                    "information": "INFO"
                }
                mapped_severity = severity_map.get(severity, "MEDIUM")
                
                # Get location info
                location = error.find(".//location")
                if location is not None:
                    file_path = location.get("file", "unknown")
                    line_number = int(location.get("line", "1"))
                else:
                    file_path = "unknown"
                    line_number = 1
                
                findings.append({
                    "file": file_path,
                    "line": line_number,
                    "severity": mapped_severity,
                    "rule_id": error_id,
                    "description": verbose,
                    "tool": "cppcheck"
                })
        
        except ET.ParseError as e:
            findings = [{
                "file": "unknown",
                "line": 1,
                "severity": "ERROR",
                "rule_id": "PARSE_ERROR",
                "description": f"Failed to parse Cppcheck output: {str(e)}",
                "tool": "cppcheck"
            }]
        
        return findings
    
    def _run_clang_tidy(self, path: Path) -> list[dict[str, Any]]:
        """
        Run Clang-Tidy on C/C++ code.
        
        Args:
            path: Path to file or directory
            
        Returns:
            List of security findings
        """
        findings = []
        
        try:
            # Get list of C/C++ files
            if path.is_file():
                files = [path]
            else:
                files = list(path.rglob("*.c")) + list(path.rglob("*.cpp")) + \
                        list(path.rglob("*.cc")) + list(path.rglob("*.cxx")) + \
                        list(path.rglob("*.h")) + list(path.rglob("*.hpp"))
            
            for file in files[:10]:  # Limit to 10 files to avoid timeout
                # Run Clang-Tidy with security checks
                cmd = [
                    "clang-tidy",
                    str(file),
                    "--checks=cert-*,bugprone-*,clang-analyzer-security*",
                    "--format-style=none",
                    "--",  # Compiler flags separator
                    "-std=c++17"
                ]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                # Parse output
                findings.extend(self._parse_clang_tidy_output(result.stdout, file))
        
        except subprocess.TimeoutExpired:
            pass  # Skip timeout files
        except Exception:
            pass  # Skip errors, Clang-Tidy is optional
        
        return findings
    
    def _parse_clang_tidy_output(self, output: str, file_path: Path) -> list[dict[str, Any]]:
        """
        Parse Clang-Tidy text output.
        
        Args:
            output: Clang-Tidy output text
            file_path: Source file path
            
        Returns:
            List of security findings
        """
        findings = []
        
        for line in output.split('\n'):
            # Look for warning/error lines
            # Format: file:line:col: warning: message [check-name]
            if ": warning:" in line or ": error:" in line:
                parts = line.split(':')
                if len(parts) >= 4:
                    try:
                        line_num = int(parts[1])
                        severity = "HIGH" if ": error:" in line else "MEDIUM"
                        
                        # Extract message and check name
                        message_part = ':'.join(parts[3:])
                        if '[' in message_part and ']' in message_part:
                            check_name = message_part[message_part.rfind('[')+1:message_part.rfind(']')]
                            description = message_part[:message_part.rfind('[')].strip()
                        else:
                            check_name = "clang-tidy"
                            description = message_part.strip()
                        
                        findings.append({
                            "file": str(file_path),
                            "line": line_num,
                            "severity": severity,
                            "rule_id": check_name,
                            "description": description,
                            "tool": "clang-tidy"
                        })
                    except (ValueError, IndexError):
                        continue
        
        return findings


def scan_cpp_file(file_path: str) -> list[dict[str, Any]]:
    """
    Convenience function to scan a C/C++ file.
    
    Args:
        file_path: Path to C/C++ file or project
        
    Returns:
        List of security findings
    """
    scanner = CppScanner()
    return scanner.scan(file_path)
