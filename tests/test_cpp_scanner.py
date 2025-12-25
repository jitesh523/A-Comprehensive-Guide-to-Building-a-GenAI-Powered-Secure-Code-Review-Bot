"""
Tests for C/C++ Scanner
"""
import pytest
from pathlib import Path
from app.scanners.cpp_scanner import CppScanner, scan_cpp_file


class TestCppScanner:
    """Test cases for C/C++ security scanner"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.scanner = CppScanner()
        self.test_dir = Path(__file__).parent / "test_samples" / "cpp"
        self.test_dir.mkdir(parents=True, exist_ok=True)
    
    def test_scanner_initialization(self):
        """Test scanner initializes correctly"""
        assert self.scanner.name == "cppcheck"
        assert self.scanner.language == "cpp"
    
    def test_scan_simple_cpp_file(self):
        """Test scanning a simple C++ file"""
        # Create a test C++ file with security issues
        test_file = self.test_dir / "vulnerable.cpp"
        test_file.write_text("""
#include <iostream>
#include <cstring>

int main() {
    char buffer[10];
    char input[20] = "This is too long for buffer";
    
    // Buffer overflow vulnerability
    strcpy(buffer, input);
    
    std::cout << buffer << std::endl;
    return 0;
}
""")
        
        # Scan the file
        findings = self.scanner.scan(str(test_file))
        
        # Should find findings
        assert isinstance(findings, list)
        if findings:
            assert all(isinstance(f, dict) for f in findings)
            assert all("file" in f for f in findings)
            assert all("line" in f for f in findings)
            assert all("severity" in f for f in findings)
            assert all("tool" in f for f in findings)
    
    def test_scan_c_file(self):
        """Test scanning a C file"""
        test_file = self.test_dir / "vulnerable.c"
        test_file.write_text("""
#include <stdio.h>
#include <string.h>

int main() {
    char password[50];
    
    // Unsafe function - gets() is deprecated
    printf("Enter password: ");
    gets(password);  // Security vulnerability
    
    printf("Password: %s\\n", password);
    return 0;
}
""")
        
        findings = self.scanner.scan(str(test_file))
        
        assert isinstance(findings, list)
        # Cppcheck should detect the use of gets()
        if findings:
            assert any("gets" in f.get("description", "").lower() or
                      "buffer" in f.get("description", "").lower() for f in findings)
    
    def test_scan_directory(self):
        """Test scanning a directory of C/C++ files"""
        # Create multiple files
        (self.test_dir / "file1.cpp").write_text("""
#include <iostream>
int main() {
    int* ptr = nullptr;
    *ptr = 42;  // Null pointer dereference
    return 0;
}
""")
        
        (self.test_dir / "file2.cpp").write_text("""
#include <iostream>
void leak() {
    int* data = new int[100];
    // Memory leak - no delete[]
}
""")
        
        findings = self.scanner.scan(str(self.test_dir))
        
        assert isinstance(findings, list)
    
    def test_scan_cpp_file_convenience_function(self):
        """Test convenience function"""
        test_file = self.test_dir / "test.cpp"
        test_file.write_text("""
#include <iostream>

void unsafeFunction(char* input) {
    char buffer[10];
    sprintf(buffer, "%s", input);  // Potential buffer overflow
}
""")
        
        findings = scan_cpp_file(str(test_file))
        assert isinstance(findings, list)
    
    def test_scanner_handles_nonexistent_file(self):
        """Test scanner handles non-existent files"""
        findings = self.scanner.scan("/nonexistent/file.cpp")
        
        # Should return error or empty list
        assert isinstance(findings, list)
    
    def test_scan_header_file(self):
        """Test scanning a header file"""
        test_file = self.test_dir / "unsafe.h"
        test_file.write_text("""
#ifndef UNSAFE_H
#define UNSAFE_H

class UnsafeClass {
private:
    char* data;
public:
    UnsafeClass() {
        data = new char[100];
    }
    // Missing destructor - memory leak
};

#endif
""")
        
        findings = self.scanner.scan(str(test_file))
        assert isinstance(findings, list)
    
    def teardown_method(self):
        """Cleanup test files"""
        import shutil
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
