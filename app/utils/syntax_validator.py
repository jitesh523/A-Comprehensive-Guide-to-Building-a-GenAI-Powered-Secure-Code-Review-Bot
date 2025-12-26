"""
Syntax Validator for Auto-Fix Engine

Validates that generated fixes are syntactically correct before applying them.
"""
import ast
import subprocess
import tempfile
from pathlib import Path
from typing import Any
import logging

logger = logging.getLogger(__name__)


class SyntaxValidator:
    """Validates syntax for different programming languages"""
    
    @staticmethod
    def validate_python(code: str) -> tuple[bool, str]:
        """
        Validate Python syntax using AST.
        
        Args:
            code: Python code to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            ast.parse(code)
            return True, ""
        except SyntaxError as e:
            return False, f"Syntax error at line {e.lineno}: {e.msg}"
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    @staticmethod
    def validate_javascript(code: str) -> tuple[bool, str]:
        """
        Validate JavaScript syntax using Node.js.
        
        Args:
            code: JavaScript code to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(code)
                temp_path = f.name
            
            # Run node --check
            result = subprocess.run(
                ['node', '--check', temp_path],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # Clean up
            Path(temp_path).unlink()
            
            if result.returncode == 0:
                return True, ""
            else:
                return False, result.stderr
        
        except subprocess.TimeoutExpired:
            return False, "Validation timeout"
        except FileNotFoundError:
            logger.warning("Node.js not found, skipping JS validation")
            return True, "Validation skipped (Node.js not available)"
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    @staticmethod
    def validate_typescript(code: str) -> tuple[bool, str]:
        """
        Validate TypeScript syntax using tsc.
        
        Args:
            code: TypeScript code to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.ts', delete=False) as f:
                f.write(code)
                temp_path = f.name
            
            # Run tsc --noEmit
            result = subprocess.run(
                ['npx', '-y', 'typescript', '--noEmit', temp_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Clean up
            Path(temp_path).unlink()
            
            if result.returncode == 0:
                return True, ""
            else:
                return False, result.stderr
        
        except subprocess.TimeoutExpired:
            return False, "Validation timeout"
        except FileNotFoundError:
            logger.warning("TypeScript not found, skipping TS validation")
            return True, "Validation skipped (TypeScript not available)"
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    @staticmethod
    def validate_go(code: str) -> tuple[bool, str]:
        """
        Validate Go syntax using go fmt.
        
        Args:
            code: Go code to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.go', delete=False) as f:
                f.write(code)
                temp_path = f.name
            
            # Run go fmt
            result = subprocess.run(
                ['go', 'fmt', temp_path],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # Clean up
            Path(temp_path).unlink()
            
            if result.returncode == 0:
                return True, ""
            else:
                return False, result.stderr
        
        except subprocess.TimeoutExpired:
            return False, "Validation timeout"
        except FileNotFoundError:
            logger.warning("Go not found, skipping Go validation")
            return True, "Validation skipped (Go not available)"
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    @staticmethod
    def validate_rust(code: str) -> tuple[bool, str]:
        """
        Validate Rust syntax using rustfmt.
        
        Args:
            code: Rust code to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.rs', delete=False) as f:
                f.write(code)
                temp_path = f.name
            
            # Run rustfmt --check
            result = subprocess.run(
                ['rustfmt', '--check', temp_path],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # Clean up
            Path(temp_path).unlink()
            
            # rustfmt returns 0 if formatted correctly
            if result.returncode == 0:
                return True, ""
            else:
                return False, result.stderr
        
        except subprocess.TimeoutExpired:
            return False, "Validation timeout"
        except FileNotFoundError:
            logger.warning("Rust not found, skipping Rust validation")
            return True, "Validation skipped (Rust not available)"
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    @classmethod
    def validate(cls, code: str, language: str) -> tuple[bool, str]:
        """
        Validate code syntax for any supported language.
        
        Args:
            code: Code to validate
            language: Programming language
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        validators = {
            'python': cls.validate_python,
            'javascript': cls.validate_javascript,
            'typescript': cls.validate_typescript,
            'go': cls.validate_go,
            'rust': cls.validate_rust,
        }
        
        validator = validators.get(language.lower())
        if validator:
            return validator(code)
        else:
            logger.warning(f"No validator for language: {language}")
            return True, f"Validation skipped (unsupported language: {language})"


def validate_fix_syntax(code: str, language: str) -> tuple[bool, str]:
    """
    Convenience function to validate fix syntax.
    
    Args:
        code: Code to validate
        language: Programming language
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    return SyntaxValidator.validate(code, language)
