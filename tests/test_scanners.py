"""
Test script to verify Bandit and ESLint scanners
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.scanners.bandit_scanner import BanditScanner
from app.scanners.eslint_scanner import ESLintScanner


async def test_bandit():
    """Test Bandit scanner"""
    print("=" * 60)
    print("Testing Bandit Scanner")
    print("=" * 60)
    
    scanner = BanditScanner()
    results = await scanner.scan("tests/")
    
    print(f"\nFound {len(results)} issues:")
    for i, finding in enumerate(results, 1):
        print(f"\n{i}. [{finding['severity']}] {finding['rule_id']}")
        print(f"   File: {finding['file']}:{finding['line']}")
        print(f"   Description: {finding['description']}")
    
    return results


async def test_eslint():
    """Test ESLint scanner"""
    print("\n" + "=" * 60)
    print("Testing ESLint Scanner")
    print("=" * 60)
    
    scanner = ESLintScanner()
    results = await scanner.scan("tests/vulnerable.js")
    
    print(f"\nFound {len(results)} issues:")
    for i, finding in enumerate(results, 1):
        print(f"\n{i}. [{finding['severity']}] {finding['rule_id']}")
        print(f"   File: {finding['file']}:{finding['line']}")
        print(f"   Description: {finding['description']}")
    
    return results


async def main():
    """Run all tests"""
    bandit_results = await test_bandit()
    eslint_results = await test_eslint()
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Bandit findings: {len(bandit_results)}")
    print(f"ESLint findings: {len(eslint_results)}")
    print(f"Total findings: {len(bandit_results) + len(eslint_results)}")
    
    if bandit_results or eslint_results:
        print("\n✅ Scanners are working correctly!")
        return 0
    else:
        print("\n⚠️  No findings detected. Check scanner configuration.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
