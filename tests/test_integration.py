"""
Integration test for scanner + context extraction
"""
import asyncio
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.scanners.scanner_with_context import ScannerWithContext


async def test_integration():
    """Test full integration of scanning + context extraction"""
    print("=" * 60)
    print("Testing Scanner + Context Integration")
    print("=" * 60)
    
    scanner = ScannerWithContext()
    
    # Scan tests directory
    results = await scanner.scan_repository("tests/")
    
    print(f"\n📊 Results Summary:")
    print(f"   Python findings: {len(results['python'])}")
    print(f"   JavaScript findings: {len(results['javascript'])}")
    
    # Show first Python finding with context
    if results['python']:
        print("\n" + "=" * 60)
        print("Sample Python Finding with Context")
        print("=" * 60)
        
        finding = results['python'][0]
        print(f"\n🔍 Finding:")
        print(f"   Tool: {finding['tool']}")
        print(f"   Severity: {finding['severity']}")
        print(f"   Rule: {finding['rule_id']}")
        print(f"   Description: {finding['description']}")
        print(f"   Location: {finding['file']}:{finding['line']}")
        
        if 'context' in finding:
            ctx = finding['context']
            print(f"\n📦 Context:")
            print(f"   Type: {ctx.get('context_type')}")
            print(f"   Function: {ctx.get('function_name', 'N/A')}")
            print(f"   Class: {ctx.get('class_name', 'N/A')}")
            print(f"   Lines: {ctx.get('context_start_line')}-{ctx.get('context_end_line')}")
            
            print(f"\n📝 Code Context:")
            print("-" * 60)
            print(ctx.get('context_code', 'N/A')[:300])
            print("-" * 60)
    
    # Show first JavaScript finding with context
    if results['javascript']:
        print("\n" + "=" * 60)
        print("Sample JavaScript Finding with Context")
        print("=" * 60)
        
        finding = results['javascript'][0]
        print(f"\n🔍 Finding:")
        print(f"   Tool: {finding['tool']}")
        print(f"   Severity: {finding['severity']}")
        print(f"   Rule: {finding['rule_id']}")
        print(f"   Description: {finding['description']}")
        print(f"   Location: {finding['file']}:{finding['line']}")
        
        if 'context' in finding:
            ctx = finding['context']
            print(f"\n📦 Context:")
            print(f"   Type: {ctx.get('context_type')}")
            print(f"   Function: {ctx.get('function_name', 'N/A')}")
            print(f"   Lines: {ctx.get('context_start_line')}-{ctx.get('context_end_line')}")
    
    print("\n" + "=" * 60)
    print("✅ Integration test complete!")
    print("=" * 60)
    
    return results


if __name__ == "__main__":
    results = asyncio.run(test_integration())
    
    # Save results to file for inspection
    with open("scan_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Full results saved to: scan_results.json")
