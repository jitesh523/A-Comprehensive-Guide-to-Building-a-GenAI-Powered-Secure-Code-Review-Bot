"""
Test file with intentional vulnerabilities for Bandit scanning
"""
import hashlib
import pickle
import subprocess

# B303: Use of insecure MD5 hash function
def weak_hash(data):
    return hashlib.md5(data.encode()).hexdigest()

# B102: Use of exec (code injection)
def dangerous_exec(user_input):
    exec(user_input)

# B105: Hardcoded password
PASSWORD = "hardcoded_password_123"

# B301: Pickle usage (deserialization vulnerability)
def unsafe_deserialize(data):
    return pickle.loads(data)

# B602: Shell injection via subprocess
def run_command(cmd):
    subprocess.Popen(cmd, shell=True)

# B101: Use of assert (should be filtered by LLM as test code)
def test_function():
    assert True, "This is a test"

# B608: Hardcoded SQL
def get_user(username):
    query = f"SELECT * FROM users WHERE username = '{username}'"
    return query
