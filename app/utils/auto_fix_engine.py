"""
Auto-Fix Engine for generating and applying security vulnerability fixes
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import difflib
import logging
from pathlib import Path

from app.llm.verifier import LLMVerifier
from app.llm.prompts import VerificationPrompts
from app.utils.fix_templates import get_template_for_rule, FixTemplate
from openai import OpenAI
from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class FixSuggestion:
    """Represents a suggested fix for a security vulnerability"""
    finding_id: Optional[int]
    rule_id: str
    file_path: str
    line_number: int
    original_code: str
    fixed_code: str
    explanation: str
    confidence: float
    imports_needed: List[str]
    diff: str
    template_used: Optional[str] = None


class AutoFixEngine:
    """
    Engine for generating intelligent code fixes using LLM and templates
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize auto-fix engine
        
        Args:
            api_key: OpenAI API key (defaults to settings.OPENAI_API_KEY)
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        if not self.api_key:
            raise ValueError("OpenAI API key not configured")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = settings.OPENAI_MODEL
        self.temperature = 0.2  # Lower temperature for more deterministic fixes
        
        logger.info("Initialized Auto-Fix Engine")
    
    async def generate_fix(
        self,
        finding: Dict[str, Any],
        use_template: bool = True
    ) -> Optional[FixSuggestion]:
        """
        Generate a fix suggestion for a security finding
        
        Args:
            finding: Security finding with context
            use_template: Try to use predefined templates first
            
        Returns:
            FixSuggestion or None if fix cannot be generated
        """
        try:
            rule_id = finding.get('rule_id', '')
            language = self._detect_language(finding.get('file', ''))
            
            # Try template-based fix first
            if use_template:
                template = get_template_for_rule(rule_id, language)
                if template:
                    logger.info(f"Using template for {rule_id}")
                    return await self._generate_fix_from_template(finding, template)
            
            # Fall back to LLM-based fix generation
            logger.info(f"Generating LLM-based fix for {rule_id}")
            return await self._generate_fix_from_llm(finding)
            
        except Exception as e:
            logger.error(f"Fix generation failed: {str(e)}")
            return None
    
    async def _generate_fix_from_template(
        self,
        finding: Dict[str, Any],
        template: FixTemplate
    ) -> FixSuggestion:
        """Generate fix using predefined template"""
        context = finding.get('context', {})
        original_code = context.get('context_code', finding.get('code', ''))
        
        # Use LLM to adapt template to specific code
        prompt = self._create_template_adaptation_prompt(
            original_code=original_code,
            template=template,
            finding=finding
        )
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a security expert that fixes code vulnerabilities. "
                               "Generate ONLY the fixed code, no explanations."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=self.temperature,
            max_tokens=1000
        )
        
        fixed_code = response.choices[0].message.content.strip()
        
        # Remove code fences if present
        fixed_code = self._clean_code_response(fixed_code)
        
        # Generate diff
        diff = self._generate_diff(original_code, fixed_code)
        
        return FixSuggestion(
            finding_id=finding.get('id'),
            rule_id=finding.get('rule_id', ''),
            file_path=finding.get('file', ''),
            line_number=finding.get('line', 0),
            original_code=original_code,
            fixed_code=fixed_code,
            explanation=template.explanation,
            confidence=0.9,  # High confidence for template-based fixes
            imports_needed=template.imports_needed,
            diff=diff,
            template_used=template.vulnerability_type
        )
    
    async def _generate_fix_from_llm(
        self,
        finding: Dict[str, Any]
    ) -> FixSuggestion:
        """Generate fix using pure LLM reasoning"""
        context = finding.get('context', {})
        original_code = context.get('context_code', finding.get('code', ''))
        
        prompt = self._create_fix_generation_prompt(finding, original_code)
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a security expert that fixes code vulnerabilities. "
                               "Provide the fixed code and a brief explanation."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=self.temperature,
            max_tokens=1500
        )
        
        response_text = response.choices[0].message.content
        
        # Parse response to extract fixed code and explanation
        fixed_code, explanation = self._parse_llm_fix_response(response_text)
        
        # Generate diff
        diff = self._generate_diff(original_code, fixed_code)
        
        return FixSuggestion(
            finding_id=finding.get('id'),
            rule_id=finding.get('rule_id', ''),
            file_path=finding.get('file', ''),
            line_number=finding.get('line', 0),
            original_code=original_code,
            fixed_code=fixed_code,
            explanation=explanation,
            confidence=0.75,  # Lower confidence for LLM-generated fixes
            imports_needed=[],
            diff=diff,
            template_used=None
        )
    
    def _create_template_adaptation_prompt(
        self,
        original_code: str,
        template: FixTemplate,
        finding: Dict[str, Any]
    ) -> str:
        """Create prompt for adapting template to specific code"""
        return f"""Fix this security vulnerability using the provided template as a guide.

**Vulnerability**: {finding.get('description', '')}
**Rule**: {finding.get('rule_id', '')}

**Original Code**:
```
{original_code}
```

**Fix Template**:
{template.template}

**Instructions**:
1. Apply the security fix shown in the template to the original code
2. Preserve variable names, function names, and code structure
3. Only change what's necessary to fix the vulnerability
4. Return ONLY the fixed code, no explanations

**Fixed Code**:
"""
    
    def _create_fix_generation_prompt(
        self,
        finding: Dict[str, Any],
        original_code: str
    ) -> str:
        """Create prompt for LLM-based fix generation"""
        return f"""Fix this security vulnerability.

**Vulnerability**: {finding.get('description', '')}
**Rule**: {finding.get('rule_id', '')}
**Severity**: {finding.get('severity', '')}
**File**: {finding.get('file', '')}
**Line**: {finding.get('line', 0)}

**Original Code**:
```
{original_code}
```

**Instructions**:
1. Provide the fixed code that resolves the security issue
2. Preserve variable names, function names, and code structure
3. Only change what's necessary to fix the vulnerability
4. After the code, provide a brief explanation (2-3 sentences)

**Response Format**:
```
[fixed code here]
```

**Explanation**: [brief explanation here]
"""
    
    def _parse_llm_fix_response(self, response: str) -> tuple[str, str]:
        """Parse LLM response to extract code and explanation"""
        # Split by explanation marker
        parts = response.split("**Explanation**:")
        
        if len(parts) == 2:
            code_part = parts[0].strip()
            explanation = parts[1].strip()
        else:
            # Try to find code block
            code_part = response
            explanation = "Security fix applied"
        
        # Extract code from code fence
        code = self._clean_code_response(code_part)
        
        return code, explanation
    
    def _clean_code_response(self, code: str) -> str:
        """Remove code fences and extra formatting from LLM response"""
        lines = code.split('\n')
        
        # Remove code fences
        if lines and lines[0].startswith('```'):
            lines = lines[1:]
        if lines and lines[-1].startswith('```'):
            lines = lines[:-1]
        
        return '\n'.join(lines).strip()
    
    def _generate_diff(self, original: str, fixed: str) -> str:
        """Generate unified diff between original and fixed code"""
        original_lines = original.splitlines(keepends=True)
        fixed_lines = fixed.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            original_lines,
            fixed_lines,
            fromfile='original',
            tofile='fixed',
            lineterm=''
        )
        
        return ''.join(diff)
    
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension"""
        ext_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.go': 'go',
            '.rs': 'rust',
            '.java': 'java',
            '.rb': 'ruby',
            '.php': 'php',
        }
        
        ext = Path(file_path).suffix.lower()
        return ext_map.get(ext, 'unknown')
    
    def validate_fix(
        self,
        original_code: str,
        fixed_code: str,
        language: str
    ) -> bool:
        """
        Validate that the fix is syntactically correct
        
        Args:
            original_code: Original code
            fixed_code: Fixed code
            language: Programming language
            
        Returns:
            True if fix is valid
        """
        # Basic validation: check that code is not empty
        if not fixed_code or not fixed_code.strip():
            logger.warning("Fixed code is empty")
            return False
        
        # Check that fix actually changed something
        if original_code.strip() == fixed_code.strip():
            logger.warning("Fix did not change the code")
            return False
        
        # Language-specific syntax validation would go here
        # For now, we'll use tree-sitter in a future iteration
        
        return True
    
    async def apply_fix(
        self,
        fix: FixSuggestion,
        dry_run: bool = True
    ) -> bool:
        """
        Apply a fix to the actual file
        
        Args:
            fix: Fix suggestion to apply
            dry_run: If True, don't actually modify the file
            
        Returns:
            True if fix was applied successfully
        """
        try:
            file_path = Path(fix.file_path)
            
            if not file_path.exists():
                logger.error(f"File not found: {file_path}")
                return False
            
            # Read current file content
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Apply the fix (simple replacement for now)
            # In production, this should use more sophisticated patching
            new_content = content.replace(fix.original_code, fix.fixed_code)
            
            if dry_run:
                logger.info(f"[DRY RUN] Would apply fix to {file_path}")
                return True
            
            # Create backup
            backup_path = file_path.with_suffix(file_path.suffix + '.backup')
            with open(backup_path, 'w') as f:
                f.write(content)
            
            # Write fixed content
            with open(file_path, 'w') as f:
                f.write(new_content)
            
            logger.info(f"Applied fix to {file_path} (backup: {backup_path})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply fix: {str(e)}")
            return False
