"""
Fix templates for common security vulnerabilities
"""
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class FixTemplate:
    """Template for fixing a specific vulnerability type"""
    vulnerability_type: str
    rule_ids: List[str]  # SAST rule IDs this applies to
    languages: List[str]
    template: str
    imports_needed: List[str]
    explanation: str


# Python Fix Templates
PYTHON_TEMPLATES = [
    FixTemplate(
        vulnerability_type="weak_crypto_md5",
        rule_ids=["B303", "B324"],
        languages=["python"],
        template="""
# Replace MD5 with bcrypt for password hashing
import bcrypt

# Old (insecure):
# password_hash = hashlib.md5(password.encode()).hexdigest()

# New (secure):
password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
""",
        imports_needed=["bcrypt"],
        explanation="MD5 is cryptographically broken. Use bcrypt for password hashing."
    ),
    
    FixTemplate(
        vulnerability_type="weak_crypto_sha1",
        rule_ids=["B303", "B324"],
        languages=["python"],
        template="""
# Replace SHA1 with SHA256 for secure hashing
import hashlib

# Old (insecure):
# hash_value = hashlib.sha1(data).hexdigest()

# New (secure):
hash_value = hashlib.sha256(data).hexdigest()
""",
        imports_needed=["hashlib"],
        explanation="SHA1 is deprecated. Use SHA256 or higher for secure hashing."
    ),
    
    FixTemplate(
        vulnerability_type="sql_injection",
        rule_ids=["B608", "B609"],
        languages=["python"],
        template="""
# Use parameterized queries to prevent SQL injection
# Old (vulnerable):
# cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")

# New (secure):
cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
""",
        imports_needed=[],
        explanation="Parameterized queries prevent SQL injection by separating SQL code from data."
    ),
    
    FixTemplate(
        vulnerability_type="command_injection",
        rule_ids=["B602", "B603", "B605", "B607"],
        languages=["python"],
        template="""
# Use subprocess with list arguments instead of shell=True
import subprocess

# Old (vulnerable):
# subprocess.call(f"ls {user_input}", shell=True)

# New (secure):
subprocess.run(["ls", user_input], shell=False, check=True)
""",
        imports_needed=["subprocess"],
        explanation="Using shell=False and list arguments prevents command injection."
    ),
    
    FixTemplate(
        vulnerability_type="hardcoded_password",
        rule_ids=["B105", "B106"],
        languages=["python"],
        template="""
# Use environment variables for sensitive data
import os

# Old (insecure):
# password = "hardcoded_password123"

# New (secure):
password = os.environ.get("DB_PASSWORD")
if not password:
    raise ValueError("DB_PASSWORD environment variable not set")
""",
        imports_needed=["os"],
        explanation="Store secrets in environment variables, never hardcode them."
    ),
    
    FixTemplate(
        vulnerability_type="path_traversal",
        rule_ids=["B608"],
        languages=["python"],
        template="""
# Validate and sanitize file paths
import os
from pathlib import Path

# Old (vulnerable):
# file_path = f"/uploads/{user_filename}"

# New (secure):
base_dir = Path("/uploads").resolve()
file_path = (base_dir / user_filename).resolve()
if not file_path.is_relative_to(base_dir):
    raise ValueError("Invalid file path")
""",
        imports_needed=["os", "pathlib.Path"],
        explanation="Validate paths to prevent directory traversal attacks."
    ),
    
    FixTemplate(
        vulnerability_type="insecure_deserialization",
        rule_ids=["B301", "B302", "B303"],
        languages=["python"],
        template="""
# Use json instead of pickle for untrusted data
import json

# Old (vulnerable):
# import pickle
# data = pickle.loads(untrusted_input)

# New (secure):
data = json.loads(untrusted_input)
""",
        imports_needed=["json"],
        explanation="pickle can execute arbitrary code. Use json for untrusted data."
    ),
]


# JavaScript/TypeScript Fix Templates
JAVASCRIPT_TEMPLATES = [
    FixTemplate(
        vulnerability_type="xss",
        rule_ids=["no-danger", "react/no-danger"],
        languages=["javascript", "typescript"],
        template="""
// Use safe React rendering instead of dangerouslySetInnerHTML
// Old (vulnerable):
// <div dangerouslySetInnerHTML={{__html: userInput}} />

// New (secure):
<div>{userInput}</div>

// Or use DOMPurify for HTML content:
import DOMPurify from 'dompurify';
<div dangerouslySetInnerHTML={{__html: DOMPurify.sanitize(userInput)}} />
""",
        imports_needed=["dompurify"],
        explanation="React escapes content by default. Use DOMPurify if HTML is needed."
    ),
    
    FixTemplate(
        vulnerability_type="eval_usage",
        rule_ids=["no-eval"],
        languages=["javascript", "typescript"],
        template="""
// Avoid eval() - use safer alternatives
// Old (vulnerable):
// eval(userInput);

// New (secure - for JSON):
JSON.parse(userInput);

// Or use Function constructor with validation:
const func = new Function('return ' + sanitizedInput);
""",
        imports_needed=[],
        explanation="eval() can execute arbitrary code. Use JSON.parse or validate input."
    ),
    
    FixTemplate(
        vulnerability_type="sql_injection_js",
        rule_ids=["security/detect-sql-injection"],
        languages=["javascript", "typescript"],
        template="""
// Use parameterized queries
// Old (vulnerable):
// db.query(`SELECT * FROM users WHERE id = ${userId}`);

// New (secure):
db.query('SELECT * FROM users WHERE id = ?', [userId]);

// Or with named parameters:
db.query('SELECT * FROM users WHERE id = :id', {id: userId});
""",
        imports_needed=[],
        explanation="Parameterized queries prevent SQL injection."
    ),
]


# Go Fix Templates
GO_TEMPLATES = [
    FixTemplate(
        vulnerability_type="sql_injection_go",
        rule_ids=["G201", "G202"],
        languages=["go"],
        template="""
// Use parameterized queries
// Old (vulnerable):
// query := fmt.Sprintf("SELECT * FROM users WHERE id = %s", userID)
// db.Query(query)

// New (secure):
db.Query("SELECT * FROM users WHERE id = $1", userID)
""",
        imports_needed=[],
        explanation="Use parameterized queries with placeholders."
    ),
    
    FixTemplate(
        vulnerability_type="weak_crypto_go",
        rule_ids=["G401", "G501"],
        languages=["go"],
        template="""
// Use SHA256 instead of MD5/SHA1
import "crypto/sha256"

// Old (insecure):
// h := md5.New()

// New (secure):
h := sha256.New()
""",
        imports_needed=["crypto/sha256"],
        explanation="Use SHA256 or higher for cryptographic hashing."
    ),
]


# Rust Fix Templates
RUST_TEMPLATES = [
    FixTemplate(
        vulnerability_type="unsafe_code",
        rule_ids=["clippy::unsafe_code"],
        languages=["rust"],
        template="""
// Avoid unsafe code when possible
// Old (potentially unsafe):
// unsafe {
//     *ptr = value;
// }

// New (safe):
// Use safe Rust abstractions like Vec, Box, Rc, Arc
let mut vec = Vec::new();
vec.push(value);
""",
        imports_needed=[],
        explanation="Prefer safe Rust abstractions over unsafe code."
    ),
]


# Combine all templates
ALL_TEMPLATES = PYTHON_TEMPLATES + JAVASCRIPT_TEMPLATES + GO_TEMPLATES + RUST_TEMPLATES


def get_template_for_rule(rule_id: str, language: str) -> Optional[FixTemplate]:
    """Get fix template for a specific rule and language"""
    for template in ALL_TEMPLATES:
        if rule_id in template.rule_ids and language in template.languages:
            return template
    return None


def get_templates_by_language(language: str) -> List[FixTemplate]:
    """Get all fix templates for a specific language"""
    return [t for t in ALL_TEMPLATES if language in t.languages]


def get_all_supported_rules() -> Dict[str, List[str]]:
    """Get all supported rule IDs by language"""
    result = {}
    for template in ALL_TEMPLATES:
        for lang in template.languages:
            if lang not in result:
                result[lang] = []
            result[lang].extend(template.rule_ids)
    return {k: list(set(v)) for k, v in result.items()}
