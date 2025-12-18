"""
Scanner Integration with Context Extraction

This module integrates SAST scanners with Tree-sitter context extraction.
"""
from typing import List, Dict, Any
from app.scanners.bandit_scanner import BanditScanner
from app.scanners.eslint_scanner import ESLintScanner
from app.scanners.gosec_scanner import GosecScanner
from app.scanners.rust_scanner import RustScanner
from app.scanners.typescript_scanner import TypeScriptScanner
from app.context.tree_sitter_slicer import TreeSitterContextSlicer
import logging
import os

logger = logging.getLogger(__name__)


class ScannerWithContext:
    """
    Wrapper that combines SAST scanning with context extraction.
    """
    
    def __init__(self):
        self.bandit = BanditScanner()
        self.eslint = ESLintScanner()
        self.gosec = GosecScanner()
        self.rust_scanner = RustScanner()
        self.typescript_scanner = TypeScriptScanner()
        self.context_slicer = TreeSitterContextSlicer()
    
    async def scan_with_context(
        self, 
        target_path: str, 
        language: str
    ) -> List[Dict[str, Any]]:
        """
        Run SAST scan and enrich findings with context.
        
        Args:
            target_path: Path to scan
            language: "python", "javascript", "go", "rust", or "typescript"
            
        Returns:
            List of findings with extracted context
        """
        # Run appropriate scanner
        language_lower = language.lower()
        if language_lower == "python":
            findings = await self.bandit.scan(target_path)
        elif language_lower in ["javascript", "js"]:
            findings = await self.eslint.scan(target_path)
        elif language_lower == "go":
            findings = await self.gosec.scan(target_path)
        elif language_lower == "rust":
            findings = await self.rust_scanner.scan(target_path)
        elif language_lower in ["typescript", "ts"]:
            findings = await self.typescript_scanner.scan(target_path)
        else:
            raise ValueError(f"Unsupported language: {language}")
        
        # Enrich each finding with context
        enriched_findings = []
        for finding in findings:
            try:
                context = self.context_slicer.extract_context(
                    file_path=finding['file'],
                    line_number=finding['line'],
                    language=language
                )
                
                # Merge finding with context
                enriched_finding = {
                    **finding,
                    "context": context
                }
                enriched_findings.append(enriched_finding)
                
            except Exception as e:
                logger.warning(
                    f"Failed to extract context for {finding['file']}:{finding['line']} - {str(e)}"
                )
                # Include finding without context
                enriched_findings.append(finding)
        
        return enriched_findings
    
    def detect_language(self, file_path: str) -> str:
        """
        Detect programming language from file extension.
        
        Args:
            file_path: Path to file
            
        Returns:
            Language name or None if not supported
        """
        ext = os.path.splitext(file_path)[1].lower()
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.go': 'go',
            '.rs': 'rust',
        }
        return language_map.get(ext)
    
    async def scan_repository(self, repo_path: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Scan entire repository for all supported languages.
        
        Args:
            repo_path: Path to repository
            
        Returns:
            Dictionary with findings grouped by language
        """
        results = {
            "python": [],
            "javascript": [],
            "typescript": [],
            "go": [],
            "rust": []
        }
        
        languages_to_scan = ["python", "javascript", "typescript", "go", "rust"]
        
        for language in languages_to_scan:
            try:
                findings = await self.scan_with_context(repo_path, language)
                results[language] = findings
                logger.info(f"Found {len(findings)} {language} findings")
            except Exception as e:
                logger.error(f"{language.capitalize()} scan failed: {str(e)}")
        
        return results
