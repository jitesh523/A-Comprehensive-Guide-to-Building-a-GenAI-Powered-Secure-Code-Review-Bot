"""
Tests for Auto-Fix Engine
"""
import pytest
import asyncio
from app.utils.auto_fix_engine import AutoFixEngine, FixSuggestion
from app.utils.fix_templates import get_template_for_rule


class TestAutoFixEngine:
    """Test suite for AutoFixEngine"""
    
    @pytest.fixture
    def engine(self):
        """Create AutoFixEngine instance"""
        return AutoFixEngine()
    
    @pytest.mark.asyncio
    async def test_generate_fix_md5_python(self, engine):
        """Test fix generation for MD5 vulnerability in Python"""
        finding = {
            'id': 1,
            'rule_id': 'B303',
            'file': 'test.py',
            'line': 10,
            'severity': 'HIGH',
            'description': 'Use of insecure MD5 hash function',
            'tool': 'bandit',
            'code': 'password_hash = hashlib.md5(password.encode()).hexdigest()',
            'context': {
                'context_code': 'import hashlib\n\npassword_hash = hashlib.md5(password.encode()).hexdigest()'
            }
        }
        
        fix = await engine.generate_fix(finding, use_template=True)
        
        assert fix is not None
        assert fix.rule_id == 'B303'
        assert 'bcrypt' in fix.fixed_code
        assert fix.confidence > 0.8
        assert 'MD5' in fix.explanation or 'bcrypt' in fix.explanation
    
    @pytest.mark.asyncio
    async def test_generate_fix_sql_injection_python(self, engine):
        """Test fix generation for SQL injection in Python"""
        finding = {
            'id': 2,
            'rule_id': 'B608',
            'file': 'test.py',
            'line': 15,
            'severity': 'HIGH',
            'description': 'Possible SQL injection',
            'tool': 'bandit',
            'code': 'cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")',
            'context': {
                'context_code': 'cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")'
            }
        }
        
        fix = await engine.generate_fix(finding, use_template=True)
        
        assert fix is not None
        assert '?' in fix.fixed_code or '%s' in fix.fixed_code
        assert fix.confidence > 0.8
    
    @pytest.mark.asyncio
    async def test_generate_fix_command_injection_python(self, engine):
        """Test fix generation for command injection in Python"""
        finding = {
            'id': 3,
            'rule_id': 'B602',
            'file': 'test.py',
            'line': 20,
            'severity': 'HIGH',
            'description': 'Use of shell=True',
            'tool': 'bandit',
            'code': 'subprocess.call(f"ls {user_input}", shell=True)',
            'context': {
                'context_code': 'import subprocess\n\nsubprocess.call(f"ls {user_input}", shell=True)'
            }
        }
        
        fix = await engine.generate_fix(finding, use_template=True)
        
        assert fix is not None
        assert 'shell=False' in fix.fixed_code or 'shell=False' in fix.explanation
        assert fix.confidence > 0.8
    
    @pytest.mark.asyncio
    async def test_generate_fix_xss_javascript(self, engine):
        """Test fix generation for XSS in JavaScript"""
        finding = {
            'id': 4,
            'rule_id': 'react/no-danger',
            'file': 'test.jsx',
            'line': 25,
            'severity': 'HIGH',
            'description': 'Dangerous property dangerouslySetInnerHTML',
            'tool': 'eslint',
            'code': '<div dangerouslySetInnerHTML={{__html: userInput}} />',
            'context': {
                'context_code': '<div dangerouslySetInnerHTML={{__html: userInput}} />'
            }
        }
        
        fix = await engine.generate_fix(finding, use_template=True)
        
        assert fix is not None
        assert 'DOMPurify' in fix.fixed_code or 'dangerouslySetInnerHTML' not in fix.fixed_code
    
    def test_validate_fix_success(self, engine):
        """Test fix validation with valid fix"""
        original = "password_hash = hashlib.md5(password.encode()).hexdigest()"
        fixed = "password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())"
        
        is_valid = engine.validate_fix(original, fixed, 'python')
        
        assert is_valid is True
    
    def test_validate_fix_empty(self, engine):
        """Test fix validation with empty fix"""
        original = "password_hash = hashlib.md5(password.encode()).hexdigest()"
        fixed = ""
        
        is_valid = engine.validate_fix(original, fixed, 'python')
        
        assert is_valid is False
    
    def test_validate_fix_no_change(self, engine):
        """Test fix validation with no changes"""
        original = "password_hash = hashlib.md5(password.encode()).hexdigest()"
        fixed = "password_hash = hashlib.md5(password.encode()).hexdigest()"
        
        is_valid = engine.validate_fix(original, fixed, 'python')
        
        assert is_valid is False
    
    def test_detect_language(self, engine):
        """Test language detection from file extension"""
        assert engine._detect_language('test.py') == 'python'
        assert engine._detect_language('test.js') == 'javascript'
        assert engine._detect_language('test.ts') == 'typescript'
        assert engine._detect_language('test.go') == 'go'
        assert engine._detect_language('test.rs') == 'rust'
    
    def test_generate_diff(self, engine):
        """Test diff generation"""
        original = "import hashlib\npassword_hash = hashlib.md5(password.encode()).hexdigest()"
        fixed = "import bcrypt\npassword_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())"
        
        diff = engine._generate_diff(original, fixed)
        
        assert '-import hashlib' in diff or '-' in diff
        assert '+import bcrypt' in diff or '+' in diff
    
    def test_clean_code_response(self, engine):
        """Test cleaning code response from LLM"""
        code_with_fence = "```python\nprint('hello')\n```"
        cleaned = engine._clean_code_response(code_with_fence)
        
        assert cleaned == "print('hello')"
        assert '```' not in cleaned


class TestFixTemplates:
    """Test suite for fix templates"""
    
    def test_get_template_for_md5_python(self):
        """Test getting template for MD5 in Python"""
        template = get_template_for_rule('B303', 'python')
        
        assert template is not None
        assert 'bcrypt' in template.template or 'SHA256' in template.template
    
    def test_get_template_for_sql_injection_python(self):
        """Test getting template for SQL injection in Python"""
        template = get_template_for_rule('B608', 'python')
        
        assert template is not None
        assert 'parameterized' in template.explanation.lower()
    
    def test_get_template_for_xss_javascript(self):
        """Test getting template for XSS in JavaScript"""
        template = get_template_for_rule('react/no-danger', 'javascript')
        
        assert template is not None
        assert 'DOMPurify' in template.template
    
    def test_get_template_nonexistent(self):
        """Test getting template for non-existent rule"""
        template = get_template_for_rule('NONEXISTENT', 'python')
        
        assert template is None


class TestFixSuggestion:
    """Test suite for FixSuggestion dataclass"""
    
    def test_fix_suggestion_creation(self):
        """Test creating FixSuggestion"""
        fix = FixSuggestion(
            finding_id=1,
            rule_id='B303',
            file_path='test.py',
            line_number=10,
            original_code='hashlib.md5(password)',
            fixed_code='bcrypt.hashpw(password, bcrypt.gensalt())',
            explanation='Use bcrypt instead of MD5',
            confidence=0.95,
            imports_needed=['bcrypt'],
            diff='- hashlib.md5\n+ bcrypt.hashpw',
            template_used='weak_crypto_md5'
        )
        
        assert fix.finding_id == 1
        assert fix.rule_id == 'B303'
        assert fix.confidence == 0.95
        assert 'bcrypt' in fix.imports_needed
