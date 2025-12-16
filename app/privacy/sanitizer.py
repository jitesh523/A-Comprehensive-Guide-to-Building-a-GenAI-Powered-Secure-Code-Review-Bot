"""
Privacy Sanitizer using Microsoft Presidio

This module detects and redacts PII and secrets before sending code to LLM.
"""
from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from typing import Dict, Any, List, Tuple
import re
import logging

logger = logging.getLogger(__name__)


class PrivacySanitizer:
    """
    Detects and redacts PII and secrets from code context.
    """
    
    # Common secret patterns
    SECRET_PATTERNS = [
        # API Keys
        (r'(?i)(api[_-]?key|apikey)[\s]*[=:]\s*["\']([a-zA-Z0-9_\-]{20,})["\']', 'API_KEY'),
        (r'(?i)(secret[_-]?key|secretkey)[\s]*[=:]\s*["\']([a-zA-Z0-9_\-]{20,})["\']', 'SECRET_KEY'),
        
        # AWS Keys
        (r'AKIA[0-9A-Z]{16}', 'AWS_ACCESS_KEY'),
        (r'(?i)aws[_-]?secret[_-]?access[_-]?key[\s]*[=:]\s*["\']([a-zA-Z0-9/+=]{40})["\']', 'AWS_SECRET_KEY'),
        
        # GitHub Tokens
        (r'ghp_[a-zA-Z0-9]{36}', 'GITHUB_TOKEN'),
        (r'gho_[a-zA-Z0-9]{36}', 'GITHUB_OAUTH_TOKEN'),
        
        # Private Keys
        (r'-----BEGIN (RSA |DSA |EC )?PRIVATE KEY-----', 'PRIVATE_KEY'),
        
        # Generic tokens
        (r'(?i)(bearer|token)[\s]*[=:]\s*["\']([a-zA-Z0-9_\-\.]{20,})["\']', 'AUTH_TOKEN'),
        
        # Database URLs
        (r'(?i)(postgres|mysql|mongodb)://[^:]+:[^@]+@[^/]+', 'DATABASE_URL'),
        
        # JWT Tokens
        (r'eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*', 'JWT_TOKEN'),
    ]
    
    def __init__(self):
        # Initialize Presidio Analyzer
        self.analyzer = AnalyzerEngine()
        
        # Initialize Presidio Anonymizer
        self.anonymizer = AnonymizerEngine()
        
        # Default PII entities to detect
        self.pii_entities = [
            "PERSON",
            "EMAIL_ADDRESS",
            "PHONE_NUMBER",
            "CREDIT_CARD",
            "IBAN_CODE",
            "IP_ADDRESS",
            "US_SSN",
            "US_PASSPORT",
            "LOCATION",
            "DATE_TIME",
            "URL",
        ]
    
    def sanitize_context(self, context: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        """
        Sanitize code context by redacting PII and secrets.
        
        Args:
            context: Context dictionary from Tree-sitter extraction
            
        Returns:
            Tuple of (sanitized_context, redaction_log)
        """
        redaction_log = []
        sanitized_context = context.copy()
        
        # Sanitize the main code context
        if 'context_code' in context:
            sanitized_code, code_redactions = self._sanitize_text(
                context['context_code'],
                "context_code"
            )
            sanitized_context['context_code'] = sanitized_code
            redaction_log.extend(code_redactions)
        
        # Sanitize imports
        if 'imports' in context and context['imports']:
            sanitized_imports = []
            for imp in context['imports']:
                sanitized_imp, imp_redactions = self._sanitize_text(imp, "import")
                sanitized_imports.append(sanitized_imp)
                redaction_log.extend(imp_redactions)
            sanitized_context['imports'] = sanitized_imports
        
        # Sanitize file path (remove username, etc.)
        if 'file' in context:
            sanitized_file = self._sanitize_file_path(context['file'])
            sanitized_context['file'] = sanitized_file
        
        return sanitized_context, redaction_log
    
    def _sanitize_text(self, text: str, field_name: str) -> Tuple[str, List[str]]:
        """
        Sanitize a text field by detecting and redacting PII and secrets.
        
        Args:
            text: Text to sanitize
            field_name: Name of the field (for logging)
            
        Returns:
            Tuple of (sanitized_text, redaction_log)
        """
        redaction_log = []
        sanitized_text = text
        
        # Step 1: Detect and redact secrets using regex patterns
        for pattern, secret_type in self.SECRET_PATTERNS:
            matches = list(re.finditer(pattern, sanitized_text))
            if matches:
                for match in reversed(matches):  # Reverse to maintain indices
                    placeholder = f"<{secret_type}_REDACTED>"
                    sanitized_text = (
                        sanitized_text[:match.start()] +
                        placeholder +
                        sanitized_text[match.end():]
                    )
                    redaction_log.append(
                        f"Redacted {secret_type} in {field_name} at position {match.start()}"
                    )
        
        # Step 2: Detect and redact PII using Presidio
        try:
            # Analyze text for PII
            analyzer_results = self.analyzer.analyze(
                text=sanitized_text,
                entities=self.pii_entities,
                language='en'
            )
            
            if analyzer_results:
                # Anonymize detected PII
                anonymized_result = self.anonymizer.anonymize(
                    text=sanitized_text,
                    analyzer_results=analyzer_results,
                    operators={
                        "DEFAULT": OperatorConfig("replace", {"new_value": "<PII_REDACTED>"}),
                        "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "<EMAIL_REDACTED>"}),
                        "PHONE_NUMBER": OperatorConfig("replace", {"new_value": "<PHONE_REDACTED>"}),
                        "PERSON": OperatorConfig("replace", {"new_value": "<NAME_REDACTED>"}),
                        "IP_ADDRESS": OperatorConfig("replace", {"new_value": "<IP_REDACTED>"}),
                    }
                )
                
                sanitized_text = anonymized_result.text
                
                for result in analyzer_results:
                    redaction_log.append(
                        f"Redacted {result.entity_type} in {field_name} "
                        f"(score: {result.score:.2f})"
                    )
        
        except Exception as e:
            logger.warning(f"Presidio analysis failed for {field_name}: {str(e)}")
        
        return sanitized_text, redaction_log
    
    def _sanitize_file_path(self, file_path: str) -> str:
        """
        Sanitize file path by removing usernames and sensitive directory names.
        
        Args:
            file_path: Original file path
            
        Returns:
            Sanitized file path
        """
        # Replace common user directory patterns
        sanitized = re.sub(r'/Users/[^/]+/', '/Users/<USERNAME>/', file_path)
        sanitized = re.sub(r'/home/[^/]+/', '/home/<USERNAME>/', sanitized)
        sanitized = re.sub(r'C:\\Users\\[^\\]+\\', 'C:\\Users\\<USERNAME>\\', sanitized)
        
        return sanitized
    
    def sanitize_finding(self, finding: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        """
        Sanitize an entire finding (SAST result + context).
        
        Args:
            finding: Finding dictionary with context
            
        Returns:
            Tuple of (sanitized_finding, redaction_log)
        """
        redaction_log = []
        sanitized_finding = finding.copy()
        
        # Sanitize the code snippet from SAST
        if 'code' in finding and finding['code']:
            sanitized_code, code_redactions = self._sanitize_text(
                finding['code'],
                "sast_code"
            )
            sanitized_finding['code'] = sanitized_code
            redaction_log.extend(code_redactions)
        
        # Sanitize the context if present
        if 'context' in finding and finding['context']:
            sanitized_context, context_redactions = self.sanitize_context(
                finding['context']
            )
            sanitized_finding['context'] = sanitized_context
            redaction_log.extend(context_redactions)
        
        # Sanitize file path
        if 'file' in finding:
            sanitized_finding['file'] = self._sanitize_file_path(finding['file'])
        
        return sanitized_finding, redaction_log
    
    def validate_sanitization(self, text: str) -> bool:
        """
        Validate that text is properly sanitized (no secrets/PII remain).
        
        Args:
            text: Text to validate
            
        Returns:
            True if safe, False if potential leaks detected
        """
        # Check for secret patterns
        for pattern, secret_type in self.SECRET_PATTERNS:
            if re.search(pattern, text):
                logger.error(f"Validation failed: {secret_type} detected in sanitized text")
                return False
        
        # Check for PII using Presidio
        try:
            analyzer_results = self.analyzer.analyze(
                text=text,
                entities=self.pii_entities,
                language='en'
            )
            
            # Filter out low-confidence detections
            high_confidence_results = [
                r for r in analyzer_results if r.score > 0.7
            ]
            
            if high_confidence_results:
                logger.error(
                    f"Validation failed: {len(high_confidence_results)} "
                    f"high-confidence PII entities detected"
                )
                return False
        
        except Exception as e:
            logger.warning(f"Validation check failed: {str(e)}")
            # Fail safe: if validation fails, assume unsafe
            return False
        
        return True
