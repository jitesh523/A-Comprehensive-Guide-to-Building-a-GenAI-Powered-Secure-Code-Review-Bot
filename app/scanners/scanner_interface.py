"""
Unified Scanner Interface

This module provides a unified interface for all language scanners.
"""
from pathlib import Path
from typing import Any, Protocol


class SecurityScanner(Protocol):
    """
    Protocol defining the interface for all security scanners.
    """
    name: str
    language: str
    
    def scan(self, file_path: str) -> list[dict[str, Any]]:
        """
        Scan a file or project for security vulnerabilities.
        
        Args:
            file_path: Path to file or project directory
            
        Returns:
            List of security findings
        """
        ...


class ScannerRegistry:
    """
    Registry for managing all available security scanners.
    """
    
    def __init__(self):
        self._scanners: dict[str, type[SecurityScanner]] = {}
        self._extension_map: dict[str, str] = {}
        self._register_default_scanners()
    
    def _register_default_scanners(self):
        """Register all default scanners."""
        # Import scanners
        from .bandit_scanner import BanditScanner
        from .eslint_scanner import ESLintScanner
        from .typescript_scanner import TypeScriptScanner
        from .gosec_scanner import GosecScanner
        from .rust_scanner import RustScanner
        from .java_scanner import JavaScanner
        from .cpp_scanner import CppScanner
        
        # Register Python scanner
        self.register("python", BanditScanner, [".py"])
        
        # Register JavaScript scanner
        self.register("javascript", ESLintScanner, [".js", ".jsx"])
        
        # Register TypeScript scanner
        self.register("typescript", TypeScriptScanner, [".ts", ".tsx"])
        
        # Register Go scanner
        self.register("go", GosecScanner, [".go"])
        
        # Register Rust scanner
        self.register("rust", RustScanner, [".rs"])
        
        # Register Java scanner
        self.register("java", JavaScanner, [".java"])
        
        # Register C/C++ scanner
        self.register("cpp", CppScanner, [".c", ".cpp", ".cc", ".cxx", ".h", ".hpp"])
    
    def register(
        self,
        language: str,
        scanner_class: type[SecurityScanner],
        extensions: list[str]
    ):
        """
        Register a scanner for a specific language.
        
        Args:
            language: Language name (e.g., "python", "java")
            scanner_class: Scanner class implementing SecurityScanner protocol
            extensions: List of file extensions (e.g., [".py", ".pyw"])
        """
        self._scanners[language] = scanner_class
        for ext in extensions:
            self._extension_map[ext.lower()] = language
    
    def get_scanner(self, language: str) -> SecurityScanner | None:
        """
        Get a scanner instance for a specific language.
        
        Args:
            language: Language name
            
        Returns:
            Scanner instance or None if not found
        """
        scanner_class = self._scanners.get(language)
        if scanner_class:
            return scanner_class()
        return None
    
    def get_scanner_for_file(self, file_path: str) -> SecurityScanner | None:
        """
        Get appropriate scanner for a file based on its extension.
        
        Args:
            file_path: Path to file
            
        Returns:
            Scanner instance or None if no scanner found
        """
        path = Path(file_path)
        ext = path.suffix.lower()
        language = self._extension_map.get(ext)
        if language:
            return self.get_scanner(language)
        return None
    
    def get_supported_languages(self) -> list[str]:
        """
        Get list of all supported languages.
        
        Returns:
            List of language names
        """
        return list(self._scanners.keys())
    
    def get_supported_extensions(self) -> list[str]:
        """
        Get list of all supported file extensions.
        
        Returns:
            List of file extensions
        """
        return list(self._extension_map.keys())


# Global scanner registry instance
scanner_registry = ScannerRegistry()


def scan_file(file_path: str, language: str | None = None) -> list[dict[str, Any]]:
    """
    Scan a file using the appropriate scanner.
    
    Args:
        file_path: Path to file
        language: Optional language override
        
    Returns:
        List of security findings
    """
    if language:
        scanner = scanner_registry.get_scanner(language)
    else:
        scanner = scanner_registry.get_scanner_for_file(file_path)
    
    if scanner:
        return scanner.scan(file_path)
    
    return [{
        "file": file_path,
        "line": 1,
        "severity": "ERROR",
        "rule_id": "UNSUPPORTED_LANGUAGE",
        "description": f"No scanner available for file: {file_path}",
        "tool": "scanner_registry"
    }]
