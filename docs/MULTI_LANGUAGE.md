# Multi-Language Support Implementation

## Overview

The Secure Code Review Bot now supports **5 programming languages**:
- Python (Bandit)
- JavaScript (ESLint)
- TypeScript (ESLint + TypeScript parser)
- Go (Gosec)
- Rust (cargo-audit + cargo-clippy)

## Scanners

### Python - Bandit
- **Tool**: [Bandit](https://github.com/PyCQA/bandit)
- **Config**: `configs/bandit.yaml`
- **Scanner**: `app/scanners/bandit_scanner.py`

### JavaScript - ESLint
- **Tool**: [ESLint](https://eslint.org/) with security plugins
- **Config**: `configs/eslint.config.mjs`
- **Scanner**: `app/scanners/eslint_scanner.py`
- **Plugins**: `eslint-plugin-security`, `eslint-plugin-no-unsanitized`

### TypeScript - ESLint
- **Tool**: ESLint with TypeScript parser
- **Config**: `configs/eslint.typescript.config.mjs`
- **Scanner**: `app/scanners/typescript_scanner.py`
- **Plugins**: `@typescript-eslint/parser`, `@typescript-eslint/eslint-plugin`

### Go - Gosec
- **Tool**: [Gosec](https://github.com/securego/gosec)
- **Config**: `configs/gosec.yaml`
- **Scanner**: `app/scanners/gosec_scanner.py`
- **Installation**: `go install github.com/securego/gosec/v2/cmd/gosec@latest`

### Rust - cargo-audit + cargo-clippy
- **Tools**: 
  - [cargo-audit](https://github.com/rustsec/rustsec) - Dependency vulnerability scanner
  - [cargo-clippy](https://github.com/rust-lang/rust-clippy) - Security lints
- **Config**: `configs/clippy.toml`
- **Scanner**: `app/scanners/rust_scanner.py`
- **Installation**: 
  - `cargo install cargo-audit`
  - `rustup component add clippy`

## Language Detection

The `ScannerWithContext` class automatically detects language based on file extensions:

```python
{
    '.py': 'python',
    '.js': 'javascript',
    '.jsx': 'javascript',
    '.ts': 'typescript',
    '.tsx': 'typescript',
    '.go': 'go',
    '.rs': 'rust',
}
```

## Usage

### Scan a specific language
```python
from app.scanners.scanner_with_context import ScannerWithContext

scanner = ScannerWithContext()
findings = await scanner.scan_with_context("/path/to/code", "go")
```

### Scan entire repository (all languages)
```python
results = await scanner.scan_repository("/path/to/repo")
# Returns: {"python": [...], "javascript": [...], "typescript": [...], "go": [...], "rust": [...]}
```

## Testing

Run tests for each scanner:

```bash
# Python scanner
pytest tests/test_scanners.py -v

# Go scanner
python tests/test_go_scanner.py

# Rust scanner
python tests/test_rust_scanner.py

# TypeScript scanner
python tests/test_typescript_scanner.py
```

## Docker Setup

The Dockerfile now includes:
- **Go 1.21.5** toolchain
- **Rust** toolchain (via rustup)
- **gosec** for Go security scanning
- **cargo-audit** and **cargo-clippy** for Rust security scanning
- **TypeScript** and ESLint plugins for TypeScript scanning

Build the updated image:
```bash
docker-compose build
```

## Configuration

Each scanner has its own configuration file in the `configs/` directory:

- `bandit.yaml` - Python security rules
- `eslint.config.mjs` - JavaScript security rules
- `eslint.typescript.config.mjs` - TypeScript security rules
- `gosec.yaml` - Go security rules
- `clippy.toml` - Rust security lints

You can customize these files to enable/disable specific rules.

## Next Steps

With multi-language support complete, the next phases will add:
1. Custom rule configuration UI
2. Metrics dashboard (Precision, Recall, F1)
3. Slack/Discord notifications
4. False positive feedback loop
