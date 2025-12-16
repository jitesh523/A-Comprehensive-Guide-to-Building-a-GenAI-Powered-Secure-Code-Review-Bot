"""
Test file with PII and secrets for sanitization testing
"""
import hashlib

# PII Examples
user_email = "john.doe@example.com"
phone_number = "+1-555-123-4567"
ssn = "123-45-6789"
credit_card = "4532-1234-5678-9010"

# Secret Examples (FAKE - for testing only)
API_KEY = "EXAMPLE_sk_test_1234567890abcdefghijklmnopqrstuvwxyz"
AWS_ACCESS_KEY = "EXAMPLE_AKIAIOSFODNN7EXAMPLE"
aws_secret_access_key = "EXAMPLE_wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
github_token = "EXAMPLE_ghp_1234567890abcdefghijklmnopqrstuv"

# Database URL with credentials
DATABASE_URL = "postgresql://admin:SuperSecret123@db.example.com:5432/mydb"

# JWT Token
jwt_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"

# Private Key
private_key = """-----BEGIN RSA PRIVATE KEY-----
MIIEpAIBAAKCAQEA1234567890abcdefghijklmnopqrstuvwxyz
-----END RSA PRIVATE KEY-----"""

# IP Address
server_ip = "192.168.1.100"

# Person names
developer_name = "Alice Johnson"
manager_name = "Bob Smith"

def process_user_data(name, email, phone):
    """
    Process user information
    """
    print(f"Processing data for {name}")
    print(f"Email: {email}")
    print(f"Phone: {phone}")
    
def authenticate_user(username, password):
    """
    Authenticate user with hardcoded credentials (vulnerability)
    """
    ADMIN_PASSWORD = "admin123"  # Hardcoded password
    if password == ADMIN_PASSWORD:
        return True
    return False
