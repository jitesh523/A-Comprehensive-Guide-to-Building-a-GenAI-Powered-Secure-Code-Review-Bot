"""
Scanner Integration with Context Extraction

This module integrates SAST scanners with Tree-sitter context extraction.
"""
from typing import List, Dict, Any
from app.scanners.bandit_scanner import BanditScanner
from app.scanners.eslint_scanner import ESLintScanner
from app.context.tree_sitter_slicer import TreeSitterContextSlicer
import logging

logger = logging.getLogger(__name__)


class ScannerWithContext:
    """
    Wrapper that combines SAST scanning with context extraction.
    """
    
    def __init__(self):
        self.bandit = BanditScanner()
        self.eslint = ESLintScanner()
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
            language: "python" or "javascript"
            
        Returns:
            List of findings with extracted context
        """
        # Run appropriate scanner
        if language.lower() == "python":
            findings = await self.bandit.scan(target_path)
        elif language.lower() in ["javascript", "js"]:
            findings = await self.eslint.scan(target_path)
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
    
    async def scan_repository(self, repo_path: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Scan entire repository for both Python and JavaScript.
        
        Args:
            repo_path: Path to repository
            
        Returns:
            Dictionary with 'python' and 'javascript' findings
        """
        results = {
            "python": [],
            "javascript": []
        }
        
        try:
            # Scan Python files
            python_findings = await self.scan_with_context(repo_path, "python")
            results["python"] = python_findings
            logger.info(f"Found {len(python_findings)} Python findings")
        except Exception as e:
            logger.error(f"Python scan failed: {str(e)}")
        
        try:
            # Scan JavaScript files
            js_findings = await self.scan_with_context(repo_path, "javascript")
            results["javascript"] = js_findings
            logger.info(f"Found {len(js_findings)} JavaScript findings")
        except Exception as e:
            logger.error(f"JavaScript scan failed: {str(e)}")
        
        return results
