"""
Test script for Go scanner (gosec)
"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.scanners.gosec_scanner import GosecScanner


async def test_gosec():
    """Test Gosec scanner"""
    print("=" * 60)
    print("Testing Gosec Scanner")
    print("=" * 60)
    
    scanner = GosecScanner()
    
    # Create a temporary vulnerable Go file for testing
    test_dir = "tests/test_samples/go"
    os.makedirs(test_dir, exist_ok=True)
    
    vulnerable_go = """package main

import (
    "crypto/md5"
    "fmt"
    "net/http"
    "os/exec"
)

func main() {
    // G401: Use of weak cryptographic primitive
    h := md5.New()
    h.Write([]byte("password"))
    
    // G104: Errors unhandled
    http.Get("http://example.com")
    
    // G204: Subprocess launched with variable
    userInput := "ls"
    cmd := exec.Command(userInput)
    cmd.Run()
    
    fmt.Println("Vulnerable Go code")
}
"""
    
    with open(f"{test_dir}/vulnerable.go", "w") as f:
        f.write(vulnerable_go)
    
    # Also create go.mod file
    with open(f"{test_dir}/go.mod", "w") as f:
        f.write("module test\n\ngo 1.21\n")
    
    results = await scanner.scan(test_dir)
    
    print(f"\nFound {len(results)} issues:")
    for i, finding in enumerate(results, 1):
        print(f"\n{i}. [{finding['severity']}] {finding['rule_id']}")
        print(f"   File: {finding['file']}:{finding['line']}")
        print(f"   Description: {finding['description']}")
    
    return results


async def main():
    """Run all tests"""
    gosec_results = await test_gosec()
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Gosec findings: {len(gosec_results)}")
    
    if gosec_results:
        print("\n✅ Gosec scanner is working correctly!")
        return 0
    else:
        print("\n⚠️  No findings detected. Check scanner configuration.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
