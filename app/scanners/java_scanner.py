"""
Java Security Scanner using SpotBugs and Find Security Bugs

This scanner integrates SpotBugs with the Find Security Bugs plugin
to detect security vulnerabilities in Java code.
"""
import subprocess
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


class JavaScanner:
    """
    Java security scanner using SpotBugs with Find Security Bugs plugin.
    """
    
    def __init__(self):
        self.name = "spotbugs"
        self.language = "java"
    
    def scan(self, file_path: str) -> list[dict[str, Any]]:
        """
        Scan a Java file or project for security vulnerabilities.
        
        Args:
            file_path: Path to Java file or project directory
            
        Returns:
            List of security findings
        """
        findings = []
        path = Path(file_path)
        
        # Determine if it's a file or directory
        if path.is_file():
            # For single file, we need to compile it first
            findings = self._scan_single_file(path)
        elif path.is_dir():
            # For directory, look for Maven or Gradle projects
            findings = self._scan_project(path)
        
        return findings
    
    def _scan_single_file(self, file_path: Path) -> list[dict[str, Any]]:
        """
        Scan a single Java file.
        
        This requires compiling the file first.
        """
        findings = []
        
        try:
            # Compile the Java file
            compile_result = subprocess.run(
                ["javac", str(file_path)],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if compile_result.returncode != 0:
                # If compilation fails, return compilation error as finding
                return [{
                    "file": str(file_path),
                    "line": 1,
                    "severity": "ERROR",
                    "rule_id": "COMPILATION_ERROR",
                    "description": f"Compilation failed: {compile_result.stderr}",
                    "tool": "javac"
                }]
            
            # Get the class file
            class_file = file_path.with_suffix('.class')
            
            if class_file.exists():
                findings = self._run_spotbugs([str(class_file)])
                # Clean up class file
                class_file.unlink()
        
        except subprocess.TimeoutExpired:
            findings = [{
                "file": str(file_path),
                "line": 1,
                "severity": "ERROR",
                "rule_id": "TIMEOUT",
                "description": "Compilation timeout exceeded",
                "tool": "javac"
            }]
        except Exception as e:
            findings = [{
                "file": str(file_path),
                "line": 1,
                "severity": "ERROR",
                "rule_id": "SCAN_ERROR",
                "description": f"Scan error: {str(e)}",
                "tool": "spotbugs"
            }]
        
        return findings
    
    def _scan_project(self, project_path: Path) -> list[dict[str, Any]]:
        """
        Scan a Java project (Maven or Gradle).
        """
        findings = []
        
        # Check for Maven project
        if (project_path / "pom.xml").exists():
            findings = self._scan_maven_project(project_path)
        # Check for Gradle project
        elif (project_path / "build.gradle").exists() or (project_path / "build.gradle.kts").exists():
            findings = self._scan_gradle_project(project_path)
        else:
            # Try to find all .class files
            class_files = list(project_path.rglob("*.class"))
            if class_files:
                findings = self._run_spotbugs([str(f) for f in class_files])
        
        return findings
    
    def _scan_maven_project(self, project_path: Path) -> list[dict[str, Any]]:
        """
        Scan a Maven project.
        """
        try:
            # Run Maven compile
            compile_result = subprocess.run(
                ["mvn", "clean", "compile", "-DskipTests"],
                cwd=str(project_path),
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if compile_result.returncode != 0:
                return [{
                    "file": str(project_path / "pom.xml"),
                    "line": 1,
                    "severity": "ERROR",
                    "rule_id": "BUILD_ERROR",
                    "description": f"Maven build failed: {compile_result.stderr}",
                    "tool": "maven"
                }]
            
            # Find target/classes directory
            classes_dir = project_path / "target" / "classes"
            if classes_dir.exists():
                return self._run_spotbugs_on_directory(classes_dir)
        
        except subprocess.TimeoutExpired:
            return [{
                "file": str(project_path / "pom.xml"),
                "line": 1,
                "severity": "ERROR",
                "rule_id": "TIMEOUT",
                "description": "Maven build timeout exceeded",
                "tool": "maven"
            }]
        except Exception as e:
            return [{
                "file": str(project_path / "pom.xml"),
                "line": 1,
                "severity": "ERROR",
                "rule_id": "SCAN_ERROR",
                "description": f"Scan error: {str(e)}",
                "tool": "maven"
            }]
        
        return []
    
    def _scan_gradle_project(self, project_path: Path) -> list[dict[str, Any]]:
        """
        Scan a Gradle project.
        """
        try:
            # Run Gradle build
            gradle_cmd = "./gradlew" if (project_path / "gradlew").exists() else "gradle"
            compile_result = subprocess.run(
                [gradle_cmd, "clean", "build", "-x", "test"],
                cwd=str(project_path),
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if compile_result.returncode != 0:
                return [{
                    "file": str(project_path / "build.gradle"),
                    "line": 1,
                    "severity": "ERROR",
                    "rule_id": "BUILD_ERROR",
                    "description": f"Gradle build failed: {compile_result.stderr}",
                    "tool": "gradle"
                }]
            
            # Find build/classes directory
            classes_dir = project_path / "build" / "classes"
            if classes_dir.exists():
                return self._run_spotbugs_on_directory(classes_dir)
        
        except subprocess.TimeoutExpired:
            return [{
                "file": str(project_path / "build.gradle"),
                "line": 1,
                "severity": "ERROR",
                "rule_id": "TIMEOUT",
                "description": "Gradle build timeout exceeded",
                "tool": "gradle"
            }]
        except Exception as e:
            return [{
                "file": str(project_path / "build.gradle"),
                "line": 1,
                "severity": "ERROR",
                "rule_id": "SCAN_ERROR",
                "description": f"Scan error: {str(e)}",
                "tool": "gradle"
            }]
        
        return []
    
    def _run_spotbugs_on_directory(self, classes_dir: Path) -> list[dict[str, Any]]:
        """
        Run SpotBugs on a directory of compiled classes.
        """
        class_files = list(classes_dir.rglob("*.class"))
        if class_files:
            return self._run_spotbugs([str(f) for f in class_files])
        return []
    
    def _run_spotbugs(self, class_files: list[str]) -> list[dict[str, Any]]:
        """
        Run SpotBugs on compiled class files.
        
        Args:
            class_files: List of paths to .class files
            
        Returns:
            List of security findings
        """
        findings = []
        
        try:
            # Create temporary output file
            output_file = Path("/tmp/spotbugs-output.xml")
            
            # Run SpotBugs with Find Security Bugs plugin
            # Note: This assumes SpotBugs is installed and in PATH
            cmd = [
                "spotbugs",
                "-textui",
                "-xml:withMessages",
                "-output", str(output_file),
                "-effort:max",
                "-low",  # Report all priority levels
                *class_files
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            # Parse XML output
            if output_file.exists():
                findings = self._parse_spotbugs_xml(output_file)
                output_file.unlink()
        
        except subprocess.TimeoutExpired:
            findings = [{
                "file": class_files[0] if class_files else "unknown",
                "line": 1,
                "severity": "ERROR",
                "rule_id": "TIMEOUT",
                "description": "SpotBugs scan timeout exceeded",
                "tool": "spotbugs"
            }]
        except Exception as e:
            findings = [{
                "file": class_files[0] if class_files else "unknown",
                "line": 1,
                "severity": "ERROR",
                "rule_id": "SCAN_ERROR",
                "description": f"SpotBugs scan error: {str(e)}",
                "tool": "spotbugs"
            }]
        
        return findings
    
    def _parse_spotbugs_xml(self, xml_file: Path) -> list[dict[str, Any]]:
        """
        Parse SpotBugs XML output.
        
        Args:
            xml_file: Path to SpotBugs XML output file
            
        Returns:
            List of security findings
        """
        findings = []
        
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            # Parse bug instances
            for bug in root.findall(".//BugInstance"):
                # Get bug details
                bug_type = bug.get("type", "UNKNOWN")
                category = bug.get("category", "UNKNOWN")
                priority = bug.get("priority", "3")
                
                # Map priority to severity
                severity_map = {"1": "HIGH", "2": "MEDIUM", "3": "LOW"}
                severity = severity_map.get(priority, "LOW")
                
                # Get source line info
                source_line = bug.find(".//SourceLine")
                if source_line is not None:
                    file_path = source_line.get("sourcepath", "unknown")
                    line_number = int(source_line.get("start", "1"))
                else:
                    file_path = "unknown"
                    line_number = 1
                
                # Get bug message
                long_message = bug.find(".//LongMessage")
                description = long_message.text if long_message is not None else bug_type
                
                findings.append({
                    "file": file_path,
                    "line": line_number,
                    "severity": severity,
                    "rule_id": bug_type,
                    "description": description,
                    "category": category,
                    "tool": "spotbugs"
                })
        
        except ET.ParseError as e:
            findings = [{
                "file": "unknown",
                "line": 1,
                "severity": "ERROR",
                "rule_id": "PARSE_ERROR",
                "description": f"Failed to parse SpotBugs output: {str(e)}",
                "tool": "spotbugs"
            }]
        
        return findings


def scan_java_file(file_path: str) -> list[dict[str, Any]]:
    """
    Convenience function to scan a Java file.
    
    Args:
        file_path: Path to Java file or project
        
    Returns:
        List of security findings
    """
    scanner = JavaScanner()
    return scanner.scan(file_path)
