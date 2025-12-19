# CI/CD Integration Guide

## Overview

The Secure Code Review Bot can be integrated into your CI/CD pipeline to automatically scan code for security vulnerabilities on every commit and pull request.

---

## Supported Platforms

- ✅ **GitHub Actions**
- ✅ **GitLab CI**
- ✅ **Jenkins**
- ✅ **Any CI/CD platform** (via CLI)

---

## Quick Start

### Command-Line Interface

The bot includes a CLI for easy CI/CD integration:

```bash
# Install dependencies
pip install -r requirements.txt

# Run security scan
python -m app.cli scan --path . --format sarif --fail-on high
```

**CLI Options**:
- `--path, -p`: Path to scan (default: current directory)
- `--language, -l`: Languages to scan (can specify multiple)
- `--format, -f`: Output format (`json`, `sarif`, `text`)
- `--output, -o`: Output file (default: stdout)
- `--fail-on`: Fail build on severity (`critical`, `high`, `medium`, `low`, `none`)
- `--max-findings`: Maximum findings to report

**Examples**:
```bash
# Scan Python code only
python -m app.cli scan --language python

# Output SARIF format
python -m app.cli scan --format sarif --output results.sarif

# Fail on HIGH or CRITICAL findings
python -m app.cli scan --fail-on high

# Scan multiple languages
python -m app.cli scan --language python --language javascript
```

---

## GitHub Actions

### Setup

1. Copy [`.github/workflows/security-scan.yml`](file:///Users/jitesh/A-Comprehensive-Guide-to-Building-a-GenAI-Powered-Secure-Code-Review-Bot/.github/workflows/security-scan.yml) to your repository

2. The workflow will automatically:
   - Run on pull requests and pushes to `main`/`develop`
   - Install all security tools (Bandit, ESLint, Gosec, etc.)
   - Scan your code for vulnerabilities
   - Upload results to GitHub Security tab (SARIF format)
   - Comment on PRs with findings
   - Fail the build if critical/high severity issues are found

### Configuration

Edit `.github/workflows/security-scan.yml`:

```yaml
# Change fail threshold
--fail-on medium  # Fail on MEDIUM or higher

# Scan specific languages only
--language python --language javascript

# Change branches
on:
  pull_request:
    branches: [ main, staging, production ]
```

### Viewing Results

- **Security Tab**: View all findings in the GitHub Security tab
- **PR Comments**: Findings are automatically commented on PRs
- **Actions Tab**: View detailed scan logs

---

## GitLab CI

### Setup

1. Copy [`.gitlab-ci.yml`](file:///Users/jitesh/A-Comprehensive-Guide-to-Building-a-GenAI-Powered-Secure-Code-Review-Bot/.gitlab-ci.yml) to your repository

2. The pipeline will:
   - Run on merge requests and main branch
   - Install security tools
   - Scan code and generate JSON report
   - Upload as GitLab SAST artifact
   - Fail pipeline on critical/high findings

### Configuration

Edit `.gitlab-ci.yml`:

```yaml
# Change fail threshold
--fail-on medium

# Scan specific paths
--path ./src

# Only run on specific branches
only:
  - merge_requests
  - main
```

### Viewing Results

- **Security Dashboard**: View findings in GitLab Security Dashboard
- **Pipeline Artifacts**: Download JSON results
- **Merge Request**: Findings appear in MR security widget

---

## Jenkins

### Setup

1. Copy [`Jenkinsfile`](file:///Users/jitesh/A-Comprehensive-Guide-to-Building-a-GenAI-Powered-Secure-Code-Review-Bot/Jenkinsfile) to your repository

2. Create a new Pipeline job in Jenkins:
   - **Pipeline Definition**: Pipeline script from SCM
   - **SCM**: Git
   - **Script Path**: Jenkinsfile

3. The pipeline will:
   - Run parallel scans for all languages
   - Aggregate results into SARIF format
   - Archive artifacts
   - Integrate with SonarQube (if configured)

### Configuration

Edit `Jenkinsfile`:

```groovy
// Change fail threshold
--fail-on medium

// Add SonarQube integration
environment {
    SONAR_HOST_URL = 'https://sonarqube.example.com'
}
```

### Viewing Results

- **Build Artifacts**: Download JSON/SARIF results
- **SonarQube**: View in SonarQube dashboard (if configured)
- **Console Output**: View scan summary in build logs

---

## Output Formats

### JSON Format

```json
{
  "total_findings": 5,
  "findings": [
    {
      "rule_id": "B303",
      "severity": "HIGH",
      "description": "Use of insecure MD5 hash function",
      "file": "app/utils/crypto.py",
      "line": 42,
      "tool": "bandit"
    }
  ]
}
```

### SARIF Format

SARIF (Static Analysis Results Interchange Format) is the industry standard for security scan results. It's supported by:
- GitHub Security tab
- GitLab Security Dashboard
- SonarQube
- Visual Studio Code
- Many other tools

### Text Format

Human-readable format for console output:

```
🔍 Found 5 security issue(s):

1. 🔴 [HIGH] B303
   File: app/utils/crypto.py:42
   Tool: bandit
   Description: Use of insecure MD5 hash function

2. 🟡 [MEDIUM] no-eval
   File: app/api/webhooks.js:15
   Tool: eslint
   Description: eval can be harmful
```

---

## Exit Codes

The CLI uses exit codes for CI/CD integration:

- **0**: Success (no findings above threshold)
- **1**: Failure (findings above threshold or scan error)

**Fail-on Thresholds**:
- `critical`: Fail only on CRITICAL findings
- `high`: Fail on HIGH or CRITICAL
- `medium`: Fail on MEDIUM, HIGH, or CRITICAL
- `low`: Fail on any finding
- `none`: Never fail (report only)

---

## Best Practices

### 1. Start with High Threshold

```bash
# Start with critical/high only
--fail-on high
```

Gradually lower the threshold as you fix issues.

### 2. Use Branch Protection

Configure your CI/CD platform to require the security scan to pass before merging:

- **GitHub**: Settings → Branches → Branch protection rules
- **GitLab**: Settings → Repository → Protected branches
- **Jenkins**: Use "Build Blocker" plugin

### 3. Review Findings Regularly

- Check the Security tab weekly
- Triage false positives using the Feedback API
- Update custom rules to disable noisy rules

### 4. Integrate with Notifications

Set up Slack/Discord notifications for critical findings:

```bash
# In your CI/CD environment
export SLACK_WEBHOOK_URL="https://hooks.slack.com/..."
export ENABLE_SLACK_NOTIFICATIONS=true
export NOTIFICATION_MIN_SEVERITY=CRITICAL
```

---

## Troubleshooting

### Scan Takes Too Long

```bash
# Scan only changed files (Git)
git diff --name-only HEAD~1 | xargs python -m app.cli scan --path

# Limit languages
python -m app.cli scan --language python --language javascript
```

### Too Many False Positives

1. Use the Feedback API to mark false positives
2. Create custom rules to disable noisy rules
3. Adjust fail threshold: `--fail-on critical`

### Missing Dependencies

Ensure all security tools are installed:

```bash
# Python
pip install bandit

# JavaScript/TypeScript
npm install -g eslint eslint-plugin-security

# Go
go install github.com/securego/gosec/v2/cmd/gosec@latest

# Rust
cargo install cargo-audit
rustup component add clippy
```

---

## Examples

### GitHub Actions with Custom Configuration

```yaml
- name: Run security scan
  run: |
    python -m app.cli scan \
      --path ./src \
      --language python \
      --language javascript \
      --format sarif \
      --output results.sarif \
      --fail-on medium \
      --max-findings 100
```

### GitLab CI with Caching

```yaml
security_scan:
  cache:
    paths:
      - .cache/pip
  script:
    - pip install --cache-dir .cache/pip -r requirements.txt
    - python -m app.cli scan --fail-on high
```

### Jenkins with Email Notifications

```groovy
post {
    failure {
        emailext (
            subject: "Security Scan Failed: ${env.JOB_NAME}",
            body: "Please review the security findings.",
            to: "security-team@example.com"
        )
    }
}
```

---

## Next Steps

- Set up branch protection rules
- Configure Slack/Discord notifications
- Review and triage findings weekly
- Gradually lower fail threshold as issues are fixed
- Integrate with SonarQube or other security platforms
