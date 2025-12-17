# Usage Examples

## Example 1: Basic PR Scan

### Scenario
Developer opens a PR with potential SQL injection vulnerability.

### Code
```python
# api/users.py
def get_user(username):
    query = f"SELECT * FROM users WHERE username = '{username}'"
    return db.execute(query)
```

### Bot Response
```markdown
🚨 **Security Finding: B608**

**Decision**: True Positive
**Confidence**: 98%
**Severity**: critical

**Reasoning**: SQL query uses string formatting with user input, 
creating a SQL injection vulnerability. The username parameter is 
directly interpolated into the query without sanitization.

**Exploitability**: Attacker can inject SQL commands via the username 
parameter, potentially accessing or modifying database contents.

**Remediation**: Use parameterized queries or an ORM:
\`\`\`python
query = "SELECT * FROM users WHERE username = %s"
return db.execute(query, (username,))
\`\`\`

**CWE**: [CWE-89](https://cwe.mitre.org/data/definitions/89.html)
```

### Developer Action
- Reviews comment
- Implements parameterized query
- Pushes fix
- Bot re-scans: ✅ No issues found

---

## Example 2: False Positive (Test Code)

### Code
```python
# tests/test_auth.py
def test_user_login():
    user = authenticate("test_user", "test_pass")
    assert user is not None
    assert user.role == "admin"
```

### Bot Response
```markdown
✅ **Security Finding: B101**

**Decision**: False Positive
**Confidence**: 99%
**Severity**: low

**Reasoning**: Function name starts with 'test_', indicating this is 
test code. Assert statements are appropriate and expected in unit tests.

**False Positive Reason**: Assert usage in test code is standard practice 
and not a security concern.
```

### Developer Action
- No action needed
- Bot correctly identified test code

---

## Example 3: Weak Cryptography

### Code
```javascript
// auth.js
function hashPassword(password) {
    return crypto.createHash('md5').update(password).digest('hex');
}
```

### Bot Response
```markdown
🚨 **Security Finding: security/detect-unsafe-crypto**

**Decision**: True Positive
**Confidence**: 95%
**Severity**: high

**Reasoning**: MD5 is used for password hashing. MD5 is cryptographically 
broken and vulnerable to collision attacks and rainbow table attacks.

**Exploitability**: Attacker who gains access to the password database 
can crack hashes using rainbow tables or brute force.

**Remediation**: Use bcrypt, scrypt, or Argon2 for password hashing:
\`\`\`javascript
const bcrypt = require('bcrypt');
const hash = await bcrypt.hash(password, 10);
\`\`\`

**CWE**: [CWE-327](https://cwe.mitre.org/data/definitions/327.html), 
[CWE-916](https://cwe.mitre.org/data/definitions/916.html)
```

---

## Example 4: Sanitized Input (False Positive)

### Code
```python
# scripts/backup.py
ALLOWED_SCRIPTS = ['backup.sh', 'cleanup.sh', 'restore.sh']

def run_maintenance_script(script_name):
    if script_name not in ALLOWED_SCRIPTS:
        raise ValueError("Invalid script")
    subprocess.run(f"./scripts/{script_name}", shell=True)
```

### Bot Response
```markdown
✅ **Security Finding: B602**

**Decision**: False Positive
**Confidence**: 92%
**Severity**: medium

**Reasoning**: While subprocess with shell=True is flagged, the input 
is validated against a whitelist of allowed scripts. This is an internal 
utility function with controlled input.

**False Positive Reason**: Input is validated against a hardcoded 
whitelist before use, mitigating command injection risk.
```

---

## Example 5: Batch Scan Results

### PR with Multiple Files

**Summary Comment**:
```markdown
🔒 **Security Scan Complete**

Found **3 verified security issues** in this PR.

See inline comments for details.

---
**Breakdown**:
- 🚨 Critical: 1
- 🚨 High: 1
- ⚠️  Medium: 1

**Files Affected**:
- `api/auth.py` (2 issues)
- `utils/crypto.py` (1 issue)
```

**Inline Comments**: Posted at specific lines in each file

---

## Testing the Bot Locally

### 1. Create Test Repository
```bash
mkdir test-repo
cd test-repo
git init
```

### 2. Add Vulnerable Code
```python
# vulnerable.py
import hashlib

def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()
```

### 3. Trigger Scan
```bash
# Option A: Via webhook (if configured)
git add vulnerable.py
git commit -m "Add password hashing"
git push origin feature-branch
# Open PR on GitHub

# Option B: Manual test
python tests/test_integration.py
```

### 4. Review Results
- Check PR comments on GitHub
- Or review `scan_results.json` locally

---

## Configuration Examples

### Adjust Sensitivity
```yaml
# configs/bandit.yaml
profiles:
  owasp_hybrid:
    include:
      - B102  # exec_used
      - B303  # md5
      # Remove B101 to reduce noise from test code
```

### Limit Findings per PR
```python
# app/tasks/scan_orchestrator.py
for finding in pr_findings[:5]:  # Change from 10 to 5
    # Process finding...
```

### Filter by File Type
```python
# Only scan Python and JavaScript
ALLOWED_EXTENSIONS = ['.py', '.js', '.jsx', '.ts', '.tsx']
pr_findings = [
    f for f in all_findings
    if any(f.get('file', '').endswith(ext) for ext in ALLOWED_EXTENSIONS)
]
```
