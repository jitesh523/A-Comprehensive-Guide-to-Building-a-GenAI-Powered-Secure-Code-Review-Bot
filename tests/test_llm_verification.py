"""
Test script for LLM verification
"""
import asyncio
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.llm.verifier import LLMVerifier
from app.scanners.scanner_with_context import ScannerWithContext
from app.privacy.sanitizer import PrivacySanitizer


async def test_llm_verification():
    """Test LLM verification with real findings"""
    print("=" * 60)
    print("Testing LLM Verification")
    print("=" * 60)
    
    # Check if API key is configured
    from app.config import settings
    if not settings.OPENAI_API_KEY:
        print("\n⚠️  OpenAI API key not configured!")
        print("   Set OPENAI_API_KEY in .env file to test LLM verification")
        return
    
    try:
        # Initialize components
        scanner = ScannerWithContext()
        sanitizer = PrivacySanitizer()
        verifier = LLMVerifier()
        
        # Validate API key
        print("\n🔑 Validating API key...")
        if not verifier.validate_api_key():
            print("❌ API key validation failed!")
            return
        print("✅ API key valid")
        
        # Scan test files
        print("\n📊 Scanning test files...")
        results = await scanner.scan_repository("tests/")
        
        python_findings = results.get('python', [])
        print(f"   Found {len(python_findings)} Python findings")
        
        if not python_findings:
            print("   No findings to verify!")
            return
        
        # Take first finding
        finding = python_findings[0]
        
        print(f"\n🔍 Original Finding:")
        print(f"   Tool: {finding['tool']}")
        print(f"   Rule: {finding['rule_id']}")
        print(f"   Severity: {finding['severity']}")
        print(f"   Description: {finding['description']}")
        print(f"   Location: {finding['file']}:{finding['line']}")
        
        # Sanitize finding
        print(f"\n🔒 Sanitizing finding...")
        sanitized_finding, redaction_log = sanitizer.sanitize_finding(finding)
        print(f"   Redactions: {len(redaction_log)}")
        
        # Verify with LLM
        print(f"\n🤖 Sending to LLM for verification...")
        verification = await verifier.verify_finding(sanitized_finding)
        
        print(f"\n📋 Verification Result:")
        print(f"   Decision: {verification.decision.value.upper()}")
        print(f"   Confidence: {verification.confidence:.2%}")
        print(f"   Reasoning: {verification.reasoning}")
        
        if verification.severity:
            print(f"   Adjusted Severity: {verification.severity.value}")
        
        if verification.exploitability:
            print(f"   Exploitability: {verification.exploitability}")
        
        if verification.remediation:
            print(f"   Remediation: {verification.remediation}")
        
        if verification.cwe_ids:
            print(f"   CWE IDs: {', '.join(verification.cwe_ids)}")
        
        # Save result
        result_data = {
            "finding": {
                "tool": finding['tool'],
                "rule_id": finding['rule_id'],
                "severity": finding['severity'],
                "description": finding['description'],
                "file": finding['file'],
                "line": finding['line']
            },
            "verification": {
                "decision": verification.decision.value,
                "confidence": verification.confidence,
                "reasoning": verification.reasoning,
                "severity": verification.severity.value if verification.severity else None,
                "exploitability": verification.exploitability,
                "remediation": verification.remediation,
                "cwe_ids": verification.cwe_ids
            }
        }
        
        with open("llm_verification_result.json", "w") as f:
            json.dump(result_data, f, indent=2)
        
        print(f"\n💾 Result saved to: llm_verification_result.json")
        print("\n✅ LLM verification test complete!")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_batch_verification():
    """Test batch verification"""
    print("\n" + "=" * 60)
    print("Testing Batch Verification")
    print("=" * 60)
    
    from app.config import settings
    if not settings.OPENAI_API_KEY:
        print("\n⚠️  OpenAI API key not configured - skipping batch test")
        return
    
    try:
        scanner = ScannerWithContext()
        sanitizer = PrivacySanitizer()
        verifier = LLMVerifier()
        
        # Scan test files
        results = await scanner.scan_repository("tests/")
        python_findings = results.get('python', [])[:3]  # Take first 3
        
        if not python_findings:
            print("   No findings to verify!")
            return
        
        print(f"\n📊 Verifying {len(python_findings)} findings in batch...")
        
        # Sanitize all findings
        sanitized_findings = []
        for finding in python_findings:
            sanitized, _ = sanitizer.sanitize_finding(finding)
            sanitized_findings.append(sanitized)
        
        # Batch verify
        verifications = await verifier.verify_batch(sanitized_findings, max_concurrent=2)
        
        print(f"\n📋 Batch Results:")
        for i, (finding, verification) in enumerate(zip(python_findings, verifications), 1):
            print(f"\n{i}. {finding['rule_id']} - {verification.decision.value.upper()}")
            print(f"   Confidence: {verification.confidence:.2%}")
            print(f"   Reasoning: {verification.reasoning[:80]}...")
        
        print("\n✅ Batch verification complete!")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n🤖 LLM Verification Test Suite")
    print("=" * 60)
    
    asyncio.run(test_llm_verification())
    # asyncio.run(test_batch_verification())  # Uncomment to test batch
