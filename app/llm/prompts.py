"""
Verification prompt templates for LLM
"""
from typing import Dict, Any


class VerificationPrompts:
    """
    Prompt templates for security finding verification.
    """
    
    SYSTEM_PROMPT = """You are a senior security engineer reviewing code for vulnerabilities.

Your task is to verify whether a SAST (Static Application Security Testing) finding is a TRUE POSITIVE or FALSE POSITIVE.

CRITICAL INSTRUCTIONS:
1. You are NOT finding new bugs - you are VERIFYING an existing SAST alert
2. Consider the FULL CONTEXT: function logic, variable names, comments, imports
3. Distinguish between:
   - Test code vs. production code
   - Internal utilities vs. exposed APIs
   - Sanitized input vs. user-controlled input
   - Intentional design vs. security flaw

DECISION CRITERIA:
- TRUE POSITIVE: The vulnerability is real and exploitable in this context
- FALSE POSITIVE: The SAST tool flagged safe code (e.g., test code, sanitized input, internal-only)
- UNCERTAIN: Not enough context to determine (rare - use sparingly)

Be conservative: if the code LOOKS vulnerable but you see sanitization or validation, mark as FALSE POSITIVE.
"""
    
    @staticmethod
    def create_verification_prompt(
        sast_tool: str,
        rule_id: str,
        severity: str,
        description: str,
        code_context: str,
        function_name: str = None,
        class_name: str = None,
        file_path: str = None,
        line_number: int = None
    ) -> str:
        """
        Create a verification prompt for a specific finding.
        
        Args:
            sast_tool: Name of SAST tool (bandit, eslint)
            rule_id: Rule ID that triggered
            severity: SAST severity
            description: SAST description
            code_context: Sanitized code context
            function_name: Function name (optional)
            class_name: Class name (optional)
            file_path: File path (optional)
            line_number: Line number (optional)
            
        Returns:
            Formatted prompt string
        """
        prompt_parts = [
            f"**SAST Finding to Verify:**",
            f"- Tool: {sast_tool}",
            f"- Rule: {rule_id}",
            f"- Severity: {severity}",
            f"- Description: {description}",
        ]
        
        if file_path:
            prompt_parts.append(f"- Location: {file_path}:{line_number}")
        
        if function_name:
            prompt_parts.append(f"- Function: {function_name}")
        
        if class_name:
            prompt_parts.append(f"- Class: {class_name}")
        
        prompt_parts.extend([
            "",
            "**Code Context:**",
            "```",
            code_context,
            "```",
            "",
            "**Your Task:**",
            "Analyze the code context and determine if this SAST finding is a TRUE POSITIVE or FALSE POSITIVE.",
            "",
            "Consider:",
            "1. Is this test code or production code?",
            "2. Is the input sanitized or validated before use?",
            "3. Is this function exposed to users or internal-only?",
            "4. Are there mitigating controls in place?",
            "5. Does the variable/function naming suggest intentional design?",
            "",
            "Provide your verification decision with reasoning."
        ])
        
        return "\n".join(prompt_parts)
    
    @staticmethod
    def create_batch_verification_prompt(findings: list) -> str:
        """
        Create a prompt for batch verification (future enhancement).
        
        Args:
            findings: List of findings to verify
            
        Returns:
            Formatted batch prompt
        """
        prompt_parts = [
            "**Batch Verification Request:**",
            f"You are verifying {len(findings)} SAST findings.",
            "",
            "For each finding, provide a verification decision.",
            ""
        ]
        
        for i, finding in enumerate(findings, 1):
            prompt_parts.extend([
                f"## Finding {i}:",
                f"- Rule: {finding.get('rule_id')}",
                f"- Description: {finding.get('description')}",
                f"- Code: {finding.get('code', 'N/A')[:100]}...",
                ""
            ])
        
        return "\n".join(prompt_parts)
    
    @staticmethod
    def create_few_shot_examples() -> str:
        """
        Create few-shot examples to improve LLM accuracy.
        
        Returns:
            Few-shot examples string
        """
        return """
**Example 1: FALSE POSITIVE (Test Code)**

SAST Finding: B101 - assert_used
Code Context:
```python
def test_user_authentication():
    user = authenticate("test_user", "test_pass")
    assert user is not None
    assert user.role == "admin"
```

Decision: FALSE POSITIVE
Reasoning: This is test code (function name starts with 'test_'). Assert statements are appropriate in tests.

---

**Example 2: TRUE POSITIVE (Weak Crypto)**

SAST Finding: B303 - md5 usage
Code Context:
```python
def hash_password(password):
    \"\"\"Hash user password for storage\"\"\"
    return hashlib.md5(password.encode()).hexdigest()
```

Decision: TRUE POSITIVE
Reasoning: MD5 is used for password hashing. This is cryptographically weak and vulnerable to rainbow table attacks. Should use bcrypt or Argon2.

---

**Example 3: FALSE POSITIVE (Sanitized Input)**

SAST Finding: B602 - subprocess with shell=True
Code Context:
```python
def run_internal_script(script_name):
    # Whitelist of allowed scripts
    ALLOWED_SCRIPTS = ['backup.sh', 'cleanup.sh']
    if script_name not in ALLOWED_SCRIPTS:
        raise ValueError("Invalid script")
    subprocess.run(f"./scripts/{script_name}", shell=True)
```

Decision: FALSE POSITIVE
Reasoning: Input is validated against a whitelist before use. Not user-controlled. Internal utility function.
"""
