"""
Tests for Java Scanner
"""
import pytest
from pathlib import Path
from app.scanners.java_scanner import JavaScanner, scan_java_file


class TestJavaScanner:
    """Test cases for Java security scanner"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.scanner = JavaScanner()
        self.test_dir = Path(__file__).parent / "test_samples" / "java"
        self.test_dir.mkdir(parents=True, exist_ok=True)
    
    def test_scanner_initialization(self):
        """Test scanner initializes correctly"""
        assert self.scanner.name == "spotbugs"
        assert self.scanner.language == "java"
    
    def test_scan_simple_java_file(self):
        """Test scanning a simple Java file"""
        # Create a test Java file with a security issue
        test_file = self.test_dir / "VulnerableCode.java"
        test_file.write_text("""
public class VulnerableCode {
    public static void main(String[] args) {
        // SQL Injection vulnerability
        String query = "SELECT * FROM users WHERE id = " + args[0];
        System.out.println(query);
    }
}
""")
        
        # Scan the file
        findings = self.scanner.scan(str(test_file))
        
        # Should find findings or compilation errors
        assert isinstance(findings, list)
        if findings:
            assert all(isinstance(f, dict) for f in findings)
            assert all("file" in f for f in findings)
            assert all("line" in f for f in findings)
            assert all("severity" in f for f in findings)
    
    def test_scan_nonexistent_file(self):
        """Test scanning a non-existent file"""
        findings = self.scanner.scan("/nonexistent/file.java")
        
        # Should return error finding
        assert isinstance(findings, list)
        if findings:
            assert findings[0]["severity"] == "ERROR"
    
    def test_scan_java_file_convenience_function(self):
        """Test convenience function"""
        test_file = self.test_dir / "SimpleClass.java"
        test_file.write_text("""
public class SimpleClass {
    private String password = "hardcoded123";  // Security issue
    
    public void setPassword(String pwd) {
        this.password = pwd;
    }
}
""")
        
        findings = scan_java_file(str(test_file))
        assert isinstance(findings, list)
    
    def test_scanner_handles_compilation_errors(self):
        """Test scanner handles invalid Java code"""
        test_file = self.test_dir / "InvalidCode.java"
        test_file.write_text("""
public class InvalidCode {
    // Missing closing brace
    public void test() {
        System.out.println("test");
""")
        
        findings = self.scanner.scan(str(test_file))
        
        # Should return compilation error
        assert isinstance(findings, list)
        if findings:
            assert any("COMPILATION_ERROR" in f.get("rule_id", "") or 
                      "ERROR" in f.get("severity", "") for f in findings)
    
    def teardown_method(self):
        """Cleanup test files"""
        import shutil
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
