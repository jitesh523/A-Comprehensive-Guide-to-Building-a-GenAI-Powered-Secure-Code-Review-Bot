"""
Test script for privacy sanitization
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.privacy.sanitizer import PrivacySanitizer
from app.context.tree_sitter_slicer import TreeSitterContextSlicer


def test_secret_detection():
    """Test secret pattern detection"""
    print("=" * 60)
    print("Testing Secret Detection")
    print("=" * 60)
    
    sanitizer = PrivacySanitizer()
    
    test_cases = [
        ("API_KEY = 'EXAMPLE_sk_test_1234567890abcdefghijklmnopqrstuv'", "API Key"),
        ("AWS_ACCESS_KEY = 'EXAMPLE_AKIAIOSFODNN7EXAMPLE'", "AWS Access Key"),
        ("github_token = 'EXAMPLE_ghp_1234567890abcdefghijklmnopqrstuv'", "GitHub Token"),
        ("DATABASE_URL = 'postgresql://testuser:testpass@db.example.com/mydb'", "Database URL"),
    ]
    
    for code, description in test_cases:
        sanitized, log = sanitizer._sanitize_text(code, "test")
        print(f"\n📝 {description}:")
        print(f"   Original: {code[:50]}...")
        print(f"   Sanitized: {sanitized[:50]}...")
        print(f"   Redactions: {len(log)}")
        
        # Validate
        is_safe = sanitizer.validate_sanitization(sanitized)
        print(f"   ✅ Safe: {is_safe}")
    
    return True


def test_pii_detection():
    """Test PII detection with Presidio"""
    print("\n" + "=" * 60)
    print("Testing PII Detection")
    print("=" * 60)
    
    sanitizer = PrivacySanitizer()
    
    test_cases = [
        ("user_email = 'john.doe@example.com'", "Email"),
        ("phone = '+1-555-123-4567'", "Phone Number"),
        ("ssn = '123-45-6789'", "SSN"),
        ("name = 'Alice Johnson'", "Person Name"),
        ("server_ip = '192.168.1.100'", "IP Address"),
    ]
    
    for code, description in test_cases:
        sanitized, log = sanitizer._sanitize_text(code, "test")
        print(f"\n📝 {description}:")
        print(f"   Original: {code}")
        print(f"   Sanitized: {sanitized}")
        print(f"   Redactions: {len(log)}")
        if log:
            print(f"   Details: {log[0]}")
    
    return True


def test_context_sanitization():
    """Test full context sanitization"""
    print("\n" + "=" * 60)
    print("Testing Context Sanitization")
    print("=" * 60)
    
    # Extract context from test file with PII
    slicer = TreeSitterContextSlicer()
    context = slicer.extract_context(
        file_path="tests/test_pii_secrets.py",
        line_number=7,
        language="python"
    )
    
    print(f"\n📦 Original Context:")
    print(f"   File: {context.get('file')}")
    print(f"   Function: {context.get('function_name')}")
    print(f"   Code length: {len(context.get('context_code', ''))}")
    
    # Sanitize the context
    sanitizer = PrivacySanitizer()
    sanitized_context, log = sanitizer.sanitize_context(context)
    
    print(f"\n🔒 Sanitized Context:")
    print(f"   File: {sanitized_context.get('file')}")
    print(f"   Redactions: {len(log)}")
    
    if log:
        print(f"\n📋 Redaction Log:")
        for entry in log[:5]:  # Show first 5
            print(f"   - {entry}")
    
    # Validate sanitization
    is_safe = sanitizer.validate_sanitization(
        sanitized_context.get('context_code', '')
    )
    print(f"\n✅ Validation: {'PASSED' if is_safe else 'FAILED'}")
    
    # Show sample of sanitized code
    print(f"\n📝 Sanitized Code Sample:")
    print("-" * 60)
    print(sanitized_context.get('context_code', '')[:300])
    print("-" * 60)
    
    return is_safe


def test_finding_sanitization():
    """Test full finding sanitization (SAST + context)"""
    print("\n" + "=" * 60)
    print("Testing Finding Sanitization")
    print("=" * 60)
    
    # Mock finding with PII
    finding = {
        "tool": "bandit",
        "severity": "HIGH",
        "rule_id": "B105",
        "description": "Hardcoded password detected",
        "file": "/Users/john.doe/project/auth.py",
        "line": 42,
        "code": "PASSWORD = 'admin123'  # Contact alice.johnson@company.com",
        "context": {
            "context_code": "def authenticate(user, password):\n    ADMIN_PASS = 'secret123'\n    if password == ADMIN_PASS:\n        return True",
            "function_name": "authenticate",
            "file": "/Users/john.doe/project/auth.py"
        }
    }
    
    sanitizer = PrivacySanitizer()
    sanitized_finding, log = sanitizer.sanitize_finding(finding)
    
    print(f"\n📊 Sanitization Results:")
    print(f"   Original file: {finding['file']}")
    print(f"   Sanitized file: {sanitized_finding['file']}")
    print(f"   Total redactions: {len(log)}")
    
    print(f"\n📝 Original code snippet:")
    print(f"   {finding['code']}")
    
    print(f"\n🔒 Sanitized code snippet:")
    print(f"   {sanitized_finding['code']}")
    
    # Validate
    is_safe = sanitizer.validate_sanitization(
        sanitized_finding.get('code', '') +
        sanitized_finding['context'].get('context_code', '')
    )
    print(f"\n✅ Final Validation: {'PASSED ✓' if is_safe else 'FAILED ✗'}")
    
    return is_safe


def main():
    """Run all sanitization tests"""
    try:
        print("\n🔐 Privacy Sanitization Test Suite")
        print("=" * 60)
        
        test_secret_detection()
        test_pii_detection()
        test_context_sanitization()
        test_finding_sanitization()
        
        print("\n" + "=" * 60)
        print("✅ All sanitization tests completed!")
        print("=" * 60)
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
