"""
Command-line interface for CI/CD integration
"""
import click
import asyncio
import json
import sys
from pathlib import Path
from typing import Optional
from app.scanners.scanner_with_context import ScannerWithContext
from app.config import settings
from app.utils.auto_fix_engine import AutoFixEngine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Secure Code Review Bot - CLI for CI/CD Integration"""
    pass


@cli.command()
@click.option('--path', '-p', default='.', help='Path to scan (default: current directory)')
@click.option('--language', '-l', multiple=True, help='Languages to scan (default: all)')
@click.option('--format', '-f', type=click.Choice(['json', 'sarif', 'text']), default='text', help='Output format')
@click.option('--output', '-o', type=click.Path(), help='Output file (default: stdout)')
@click.option('--fail-on', type=click.Choice(['critical', 'high', 'medium', 'low', 'none']), default='critical', help='Fail build on severity')
@click.option('--max-findings', type=int, default=None, help='Maximum findings to report')
@click.option('--suggest-fixes', is_flag=True, help='Generate fix suggestions for findings')
@click.option('--auto-fix', is_flag=True, help='Automatically apply fixes (use with caution!)')
def scan(path: str, language: tuple, format: str, output: Optional[str], fail_on: str, max_findings: Optional[int], suggest_fixes: bool, auto_fix: bool):
    """
    Scan code for security vulnerabilities.
    
    Examples:
        secure-code-bot scan --path ./src --language python
        secure-code-bot scan --format sarif --output results.sarif
        secure-code-bot scan --fail-on high
        secure-code-bot scan --suggest-fixes
        secure-code-bot scan --auto-fix --path ./src
    """
    asyncio.run(run_scan(path, language, format, output, fail_on, max_findings, suggest_fixes, auto_fix))


async def run_scan(path: str, languages: tuple, format: str, output: Optional[str], fail_on: str, max_findings: Optional[int], suggest_fixes: bool, auto_fix: bool):
    """Execute the scan"""
    try:
        scanner = ScannerWithContext()
        
        # Determine languages to scan
        if languages:
            langs_to_scan = list(languages)
        else:
            langs_to_scan = ["python", "javascript", "typescript", "go", "rust"]
        
        # Run scans
        all_findings = []
        for lang in langs_to_scan:
            try:
                findings = await scanner.scan_with_context(path, lang)
                all_findings.extend(findings)
                logger.info(f"Found {len(findings)} {lang} findings")
            except Exception as e:
                logger.warning(f"Failed to scan {lang}: {str(e)}")
        
        # Limit findings if specified
        if max_findings and len(all_findings) > max_findings:
            all_findings = all_findings[:max_findings]
        
        # Generate fixes if requested
        if suggest_fixes or auto_fix:
            fix_engine = AutoFixEngine()
            for finding in all_findings:
                try:
                    fix = await fix_engine.generate_fix(finding)
                    if fix:
                        finding['fix_suggestion'] = {
                            'fixed_code': fix.fixed_code,
                            'explanation': fix.explanation,
                            'confidence': fix.confidence,
                            'diff': fix.diff
                        }
                        
                        # Apply fix if auto-fix is enabled
                        if auto_fix:
                            success = await fix_engine.apply_fix(fix, dry_run=False)
                            finding['fix_applied'] = success
                            if success:
                                logger.info(f"✅ Applied fix to {fix.file_path}:{fix.line_number}")
                except Exception as e:
                    logger.warning(f"Failed to generate fix: {str(e)}")
        
        # Format output
        if format == 'json':
            output_data = format_json(all_findings)
        elif format == 'sarif':
            output_data = format_sarif(all_findings, path)
        else:
            output_data = format_text(all_findings)
        
        # Write output
        if output:
            Path(output).write_text(output_data)
            logger.info(f"Results written to {output}")
        else:
            click.echo(output_data)
        
        # Determine exit code
        exit_code = determine_exit_code(all_findings, fail_on)
        
        if exit_code != 0:
            logger.error(f"Build failed: Found findings with severity >= {fail_on}")
        
        sys.exit(exit_code)
        
    except Exception as e:
        logger.error(f"Scan failed: {str(e)}")
        sys.exit(1)


def format_json(findings: list) -> str:
    """Format findings as JSON"""
    return json.dumps({
        "total_findings": len(findings),
        "findings": findings
    }, indent=2)


def format_sarif(findings: list, scan_path: str) -> str:
    """Format findings as SARIF (Static Analysis Results Interchange Format)"""
    sarif = {
        "version": "2.1.0",
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "Secure Code Review Bot",
                        "version": "1.0.0",
                        "informationUri": "https://github.com/jitesh523/A-Comprehensive-Guide-to-Building-a-GenAI-Powered-Secure-Code-Review-Bot"
                    }
                },
                "results": []
            }
        ]
    }
    
    for finding in findings:
        result = {
            "ruleId": finding.get("rule_id", "unknown"),
            "level": map_severity_to_sarif(finding.get("severity", "warning")),
            "message": {
                "text": finding.get("description", "Security issue found")
            },
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": finding.get("file", "unknown")
                        },
                        "region": {
                            "startLine": finding.get("line", 1)
                        }
                    }
                }
            ]
        }
        sarif["runs"][0]["results"].append(result)
    
    return json.dumps(sarif, indent=2)


def format_text(findings: list) -> str:
    """Format findings as human-readable text"""
    if not findings:
        return "✅ No security issues found!"
    
    output = [f"\n🔍 Found {len(findings)} security issue(s):\n"]
    
    for i, finding in enumerate(findings, 1):
        severity = finding.get("severity", "UNKNOWN")
        emoji = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(severity, "⚠️")
        
        output.append(f"{i}. {emoji} [{severity}] {finding.get('rule_id', 'unknown')}")
        output.append(f"   File: {finding.get('file', 'unknown')}:{finding.get('line', '?')}")
        output.append(f"   Tool: {finding.get('tool', 'unknown')}")
        output.append(f"   Description: {finding.get('description', 'No description')}")
        output.append("")
    
    return "\n".join(output)


def map_severity_to_sarif(severity: str) -> str:
    """Map internal severity to SARIF level"""
    mapping = {
        "CRITICAL": "error",
        "HIGH": "error",
        "MEDIUM": "warning",
        "LOW": "note"
    }
    return mapping.get(severity.upper(), "warning")


def determine_exit_code(findings: list, fail_on: str) -> int:
    """Determine exit code based on findings and fail-on threshold"""
    if fail_on == "none":
        return 0
    
    severity_levels = {
        "low": 1,
        "medium": 2,
        "high": 3,
        "critical": 4
    }
    
    threshold = severity_levels.get(fail_on.lower(), 4)
    
    for finding in findings:
        severity = finding.get("severity", "").lower()
        if severity_levels.get(severity, 0) >= threshold:
            return 1
    
    return 0


@cli.command()
@click.option('--finding-id', required=True, type=int, help='Finding ID to fix')
@click.option('--dry-run', is_flag=True, help='Preview fix without applying')
def fix(finding_id: int, dry_run: bool):
    """
    Apply a fix suggestion for a specific finding.
    
    Example:
        secure-code-bot fix --finding-id 123
        secure-code-bot fix --finding-id 123 --dry-run
    """
    asyncio.run(apply_fix(finding_id, dry_run))


async def apply_fix(finding_id: int, dry_run: bool):
    """Apply a fix for a specific finding"""
    try:
        # This would typically load the finding from database
        # For now, we'll show a placeholder
        logger.info(f"Loading finding #{finding_id}...")
        click.echo(f"Fix command for finding #{finding_id}")
        click.echo(f"Dry run: {dry_run}")
        click.echo("\nNote: This feature requires database integration to load findings.")
        click.echo("Use 'scan --suggest-fixes' or 'scan --auto-fix' instead.")
    except Exception as e:
        logger.error(f"Failed to apply fix: {str(e)}")
        sys.exit(1)


@cli.command()
def version():
    """Show version information"""
    click.echo("Secure Code Review Bot v1.0.0")
    click.echo(f"Supported languages: Python, JavaScript, TypeScript, Go, Rust")
    click.echo(f"Features: Auto-fix, Context-aware scanning, LLM verification")


if __name__ == '__main__':
    cli()
