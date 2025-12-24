# Auto-Fix Feature

## Overview

The Secure Code Review Bot now includes **intelligent auto-fix** capabilities that generate actual code patches for security vulnerabilities using LLM and predefined templates.

---

## How It Works

1. **Detection**: SAST tools find potential vulnerabilities
2. **Verification**: LLM verifies if it's a real issue
3. **Fix Generation**: Auto-fix engine generates a code patch
4. **Validation**: Fix is validated for syntax correctness
5. **Application**: Fix can be applied automatically or reviewed first

---

## Usage

### CLI - Suggest Fixes

Generate fix suggestions without applying them:

```bash
python -m app.cli scan --path . --suggest-fixes
```

Output includes:
- Original code
- Fixed code
- Diff preview
- Explanation
- Confidence score

### CLI - Auto-Fix

Automatically apply fixes (creates backups):

```bash
python -m app.cli scan --path ./src --auto-fix
```

**⚠️ Warning**: This modifies your code files. Always commit your changes first!

### CLI - Dry Run

Preview what would be fixed:

```bash
python -m app.cli scan --path . --auto-fix --dry-run
```

---

## Supported Vulnerability Types

### Python

| Vulnerability | Rule IDs | Fix |
|--------------|----------|-----|
| Weak crypto (MD5) | B303, B324 | Replace with bcrypt |
| Weak crypto (SHA1) | B303, B324 | Replace with SHA256 |
| SQL injection | B608, B609 | Parameterized queries |
| Command injection | B602, B603, B605, B607 | subprocess with shell=False |
| Hardcoded passwords | B105, B106 | Environment variables |
| Path traversal | B608 | Path validation |
| Insecure deserialization | B301, B302, B303 | Use json instead of pickle |

### JavaScript/TypeScript

| Vulnerability | Rule IDs | Fix |
|--------------|----------|-----|
| XSS | no-danger, react/no-danger | DOMPurify sanitization |
| eval() usage | no-eval | JSON.parse or validation |
| SQL injection | security/detect-sql-injection | Parameterized queries |

### Go

| Vulnerability | Rule IDs | Fix |
|--------------|----------|-----|
| SQL injection | G201, G202 | Parameterized queries |
| Weak crypto | G401, G501 | SHA256 instead of MD5/SHA1 |

### Rust

| Vulnerability | Rule IDs | Fix |
|--------------|----------|-----|
| Unsafe code | clippy::unsafe_code | Safe Rust abstractions |

---

## Example

### Before

```python
import hashlib

password_hash = hashlib.md5(password.encode()).hexdigest()
```

### After (Auto-Fixed)

```python
import bcrypt

password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
```

### Explanation

> MD5 is cryptographically broken and vulnerable to rainbow table attacks. Use bcrypt for password hashing, which includes built-in salting and is designed to be slow to resist brute-force attacks.

---

## Fix Generation Process

### Template-Based Fixes (High Confidence: 90%)

1. Match rule ID to predefined template
2. LLM adapts template to specific code
3. Preserves variable names and structure
4. Validates syntax

### LLM-Based Fixes (Medium Confidence: 75%)

1. LLM analyzes vulnerability context
2. Generates custom fix
3. Explains reasoning
4. Validates syntax

---

## Safety Guarantees

✅ **Syntax Validation**: All fixes validated before application  
✅ **Minimal Changes**: Only modify affected lines  
✅ **Automatic Backups**: Original files backed up as `.backup`  
✅ **Diff Preview**: Review changes before applying  
✅ **Confidence Scores**: Know how reliable each fix is  

---

## Configuration

### Environment Variables

```bash
# Enable/disable auto-fix
ENABLE_AUTO_FIX=true

# Minimum confidence to apply fixes automatically
AUTO_FIX_MIN_CONFIDENCE=0.8

# Create backups before applying fixes
AUTO_FIX_CREATE_BACKUP=true
```

---

## Limitations

### What Auto-Fix CAN Do

- Fix simple, well-defined vulnerabilities
- Replace insecure functions with secure alternatives
- Add input validation
- Update import statements

### What Auto-Fix CANNOT Do

- Refactor complex business logic
- Fix architectural issues
- Understand domain-specific requirements
- Test that fixes don't break functionality

**Always review and test auto-generated fixes!**

---

## Best Practices

### 1. Start with Suggestions

```bash
# First, see what would be fixed
python -m app.cli scan --suggest-fixes
```

### 2. Review Diffs Carefully

Check the diff output to understand what will change.

### 3. Commit Before Auto-Fix

```bash
git commit -am "Before auto-fix"
python -m app.cli scan --auto-fix
git diff  # Review changes
```

### 4. Test After Fixing

```bash
# Run your tests
pytest
npm test

# Manual testing
python -m app.main
```

### 5. Use in CI/CD Carefully

```yaml
# Good: Suggest fixes in PR comments
- run: python -m app.cli scan --suggest-fixes

# Risky: Auto-fix in CI (only for trusted repos)
- run: python -m app.cli scan --auto-fix
```

---

## API Integration

### Generate Fix Programmatically

```python
from app.utils.auto_fix_engine import AutoFixEngine

engine = AutoFixEngine()

# Generate fix
fix = await engine.generate_fix(finding)

if fix:
    print(f"Confidence: {fix.confidence}")
    print(f"Diff:\n{fix.diff}")
    
    # Apply fix
    success = await engine.apply_fix(fix, dry_run=False)
```

---

## Troubleshooting

### Fix Not Generated

**Possible reasons**:
- Vulnerability type not supported yet
- Code context insufficient
- LLM API error

**Solution**: Check logs for details, try with `--suggest-fixes` first

### Fix Breaks Code

**Solution**:
1. Restore from backup: `mv file.py.backup file.py`
2. Review the diff to understand what changed
3. Report issue with code example

### Low Confidence Fixes

Fixes with confidence < 0.7 may need manual review. Consider:
- Reviewing the suggested fix
- Applying manually with modifications
- Providing feedback to improve future fixes

---

## Future Enhancements

- [ ] Tree-sitter syntax validation
- [ ] Multi-line fix support
- [ ] Import optimization
- [ ] Test generation for fixes
- [ ] Fix learning from feedback
- [ ] IDE integration (VS Code, JetBrains)

---

## Contributing

Found a vulnerability type that should have auto-fix? 

1. Add template to `app/utils/fix_templates.py`
2. Add tests to `tests/test_auto_fix_engine.py`
3. Submit PR!

---

## Support

- 🐛 **Bugs**: [GitHub Issues](https://github.com/jitesh523/A-Comprehensive-Guide-to-Building-a-GenAI-Powered-Secure-Code-Review-Bot/issues)
- 💬 **Questions**: [GitHub Discussions](https://github.com/jitesh523/A-Comprehensive-Guide-to-Building-a-GenAI-Powered-Secure-Code-Review-Bot/discussions)
