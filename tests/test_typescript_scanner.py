"""
Test script for TypeScript scanner (ESLint with TypeScript)
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.scanners.typescript_scanner import TypeScriptScanner


async def test_typescript():
    """Test TypeScript scanner"""
    print("=" * 60)
    print("Testing TypeScript Scanner")
    print("=" * 60)
    
    scanner = TypeScriptScanner()
    
    # Create a temporary vulnerable TypeScript file for testing
    test_dir = "tests/test_samples/typescript"
    os.makedirs(test_dir, exist_ok=True)
    
    vulnerable_ts = """// Vulnerable TypeScript code for testing

// Security issue: eval usage
function executeCode(userInput: string) {
    eval(userInput);
}

// Security issue: unsafe any type
function processData(data: any) {
    return data.toString();
}

// Security issue: non-literal RegExp
function validateInput(pattern: string, input: string) {
    const regex = new RegExp(pattern);
    return regex.test(input);
}

// Security issue: innerHTML usage
function renderHTML(html: string) {
    document.body.innerHTML = html;
}

// Security issue: no input sanitization
function createURL(userInput: string) {
    window.location.href = userInput;
}

executeCode("console.log('test')");
processData({ test: 123 });
validateInput(".*", "test");
renderHTML("<div>Test</div>");
createURL("http://example.com");
"""
    
    with open(f"{test_dir}/vulnerable.ts", "w") as f:
        f.write(vulnerable_ts)
    
    results = await scanner.scan(f"{test_dir}/vulnerable.ts")
    
    print(f"\nFound {len(results)} issues:")
    for i, finding in enumerate(results, 1):
        print(f"\n{i}. [{finding['severity']}] {finding['rule_id']}")
        print(f"   File: {finding['file']}:{finding['line']}")
        print(f"   Description: {finding['description']}")
    
    return results


async def main():
    """Run all tests"""
    ts_results = await test_typescript()
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"TypeScript findings: {len(ts_results)}")
    
    if ts_results:
        print("\n✅ TypeScript scanner is working correctly!")
        return 0
    else:
        print("\n⚠️  No findings detected. Check scanner configuration.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
