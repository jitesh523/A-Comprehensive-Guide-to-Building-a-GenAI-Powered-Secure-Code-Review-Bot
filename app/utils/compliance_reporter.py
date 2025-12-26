"""
Compliance Reporter

Generates compliance reports for various standards:
- SOC2 (System and Organization Controls 2)
- GDPR (General Data Protection Regulation)
- HIPAA (Health Insurance Portability and Accountability Act)
- PCI-DSS (Payment Card Industry Data Security Standard)
"""
from datetime import datetime
from typing import Any
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


class ComplianceReporter:
    """Generate compliance reports from security scan results"""
    
    def __init__(self):
        self.report_version = "1.0"
    
    def generate_soc2_report(
        self,
        scan_results: list[dict[str, Any]],
        project_name: str
    ) -> dict[str, Any]:
        """
        Generate SOC2 compliance report.
        
        SOC2 focuses on:
        - Security
        - Availability
        - Processing Integrity
        - Confidentiality
        - Privacy
        
        Args:
            scan_results: List of security findings
            project_name: Name of the project
            
        Returns:
            SOC2 compliance report
        """
        # Categorize findings by SOC2 principles
        security_findings = []
        confidentiality_findings = []
        privacy_findings = []
        
        for finding in scan_results:
            rule_id = finding.get("rule_id", "").lower()
            description = finding.get("description", "").lower()
            
            # Security principle
            if any(keyword in rule_id or keyword in description 
                   for keyword in ["injection", "xss", "csrf", "auth", "crypto"]):
                security_findings.append(finding)
            
            # Confidentiality principle
            if any(keyword in rule_id or keyword in description
                   for keyword in ["secret", "password", "key", "token", "credential"]):
                confidentiality_findings.append(finding)
            
            # Privacy principle
            if any(keyword in rule_id or keyword in description
                   for keyword in ["pii", "personal", "gdpr", "privacy"]):
                privacy_findings.append(finding)
        
        # Calculate compliance score
        total_findings = len(scan_results)
        critical_findings = len([f for f in scan_results if f.get("severity") == "CRITICAL"])
        high_findings = len([f for f in scan_results if f.get("severity") == "HIGH"])
        
        # Simple scoring: 100 - (critical*10 + high*5)
        compliance_score = max(0, 100 - (critical_findings * 10 + high_findings * 5))
        
        return {
            "report_type": "SOC2",
            "version": self.report_version,
            "generated_at": datetime.utcnow().isoformat(),
            "project_name": project_name,
            "compliance_score": compliance_score,
            "status": "COMPLIANT" if compliance_score >= 80 else "NON_COMPLIANT",
            "summary": {
                "total_findings": total_findings,
                "critical_findings": critical_findings,
                "high_findings": high_findings,
                "security_findings": len(security_findings),
                "confidentiality_findings": len(confidentiality_findings),
                "privacy_findings": len(privacy_findings)
            },
            "principles": {
                "security": {
                    "status": "PASS" if len(security_findings) == 0 else "FAIL",
                    "findings_count": len(security_findings),
                    "findings": security_findings[:10]  # Top 10
                },
                "confidentiality": {
                    "status": "PASS" if len(confidentiality_findings) == 0 else "FAIL",
                    "findings_count": len(confidentiality_findings),
                    "findings": confidentiality_findings[:10]
                },
                "privacy": {
                    "status": "PASS" if len(privacy_findings) == 0 else "FAIL",
                    "findings_count": len(privacy_findings),
                    "findings": privacy_findings[:10]
                }
            },
            "recommendations": self._generate_soc2_recommendations(
                security_findings,
                confidentiality_findings,
                privacy_findings
            )
        }
    
    def generate_gdpr_report(
        self,
        scan_results: list[dict[str, Any]],
        project_name: str
    ) -> dict[str, Any]:
        """
        Generate GDPR compliance report.
        
        GDPR focuses on:
        - Data protection
        - Privacy by design
        - Data breach notification
        - Right to be forgotten
        
        Args:
            scan_results: List of security findings
            project_name: Name of the project
            
        Returns:
            GDPR compliance report
        """
        # Find PII-related findings
        pii_findings = []
        encryption_findings = []
        access_control_findings = []
        
        for finding in scan_results:
            rule_id = finding.get("rule_id", "").lower()
            description = finding.get("description", "").lower()
            
            if any(keyword in rule_id or keyword in description
                   for keyword in ["pii", "personal", "email", "phone", "address"]):
                pii_findings.append(finding)
            
            if any(keyword in rule_id or keyword in description
                   for keyword in ["encrypt", "crypto", "hash"]):
                encryption_findings.append(finding)
            
            if any(keyword in rule_id or keyword in description
                   for keyword in ["auth", "access", "permission", "rbac"]):
                access_control_findings.append(finding)
        
        # GDPR compliance score
        critical_pii = len([f for f in pii_findings if f.get("severity") in ["CRITICAL", "HIGH"]])
        compliance_score = max(0, 100 - (critical_pii * 15))
        
        return {
            "report_type": "GDPR",
            "version": self.report_version,
            "generated_at": datetime.utcnow().isoformat(),
            "project_name": project_name,
            "compliance_score": compliance_score,
            "status": "COMPLIANT" if compliance_score >= 85 else "NON_COMPLIANT",
            "summary": {
                "pii_findings": len(pii_findings),
                "encryption_findings": len(encryption_findings),
                "access_control_findings": len(access_control_findings)
            },
            "requirements": {
                "data_protection": {
                    "status": "PASS" if len(pii_findings) == 0 else "FAIL",
                    "findings": pii_findings[:10]
                },
                "encryption": {
                    "status": "PASS" if len(encryption_findings) == 0 else "FAIL",
                    "findings": encryption_findings[:10]
                },
                "access_control": {
                    "status": "PASS" if len(access_control_findings) == 0 else "FAIL",
                    "findings": access_control_findings[:10]
                }
            },
            "recommendations": self._generate_gdpr_recommendations(pii_findings)
        }
    
    def generate_hipaa_report(
        self,
        scan_results: list[dict[str, Any]],
        project_name: str
    ) -> dict[str, Any]:
        """
        Generate HIPAA compliance report.
        
        HIPAA focuses on:
        - Protected Health Information (PHI) security
        - Access controls
        - Audit controls
        - Encryption
        
        Args:
            scan_results: List of security findings
            project_name: Name of the project
            
        Returns:
            HIPAA compliance report
        """
        phi_findings = []
        encryption_findings = []
        audit_findings = []
        
        for finding in scan_results:
            rule_id = finding.get("rule_id", "").lower()
            description = finding.get("description", "").lower()
            
            if any(keyword in rule_id or keyword in description
                   for keyword in ["phi", "health", "medical", "patient"]):
                phi_findings.append(finding)
            
            if any(keyword in rule_id or keyword in description
                   for keyword in ["encrypt", "crypto", "tls", "ssl"]):
                encryption_findings.append(finding)
            
            if any(keyword in rule_id or keyword in description
                   for keyword in ["log", "audit", "track"]):
                audit_findings.append(finding)
        
        compliance_score = max(0, 100 - (len(phi_findings) * 20))
        
        return {
            "report_type": "HIPAA",
            "version": self.report_version,
            "generated_at": datetime.utcnow().isoformat(),
            "project_name": project_name,
            "compliance_score": compliance_score,
            "status": "COMPLIANT" if compliance_score >= 90 else "NON_COMPLIANT",
            "summary": {
                "phi_findings": len(phi_findings),
                "encryption_findings": len(encryption_findings),
                "audit_findings": len(audit_findings)
            },
            "safeguards": {
                "technical": {
                    "encryption": "PASS" if len(encryption_findings) == 0 else "FAIL",
                    "access_control": "PASS" if len([f for f in scan_results 
                                                     if "auth" in f.get("rule_id", "").lower()]) == 0 else "FAIL"
                },
                "administrative": {
                    "audit_controls": "PASS" if len(audit_findings) == 0 else "FAIL"
                }
            },
            "recommendations": self._generate_hipaa_recommendations(phi_findings)
        }
    
    def _generate_soc2_recommendations(
        self,
        security_findings: list,
        confidentiality_findings: list,
        privacy_findings: list
    ) -> list[str]:
        """Generate SOC2-specific recommendations"""
        recommendations = []
        
        if security_findings:
            recommendations.append("Implement secure coding practices to address security vulnerabilities")
        if confidentiality_findings:
            recommendations.append("Implement secrets management and encryption for sensitive data")
        if privacy_findings:
            recommendations.append("Implement privacy controls and data protection measures")
        
        return recommendations
    
    def _generate_gdpr_recommendations(self, pii_findings: list) -> list[str]:
        """Generate GDPR-specific recommendations"""
        recommendations = []
        
        if pii_findings:
            recommendations.extend([
                "Implement data minimization principles",
                "Add encryption for personal data at rest and in transit",
                "Implement access controls for PII",
                "Add audit logging for PII access",
                "Implement data retention policies"
            ])
        
        return recommendations
    
    def _generate_hipaa_recommendations(self, phi_findings: list) -> list[str]:
        """Generate HIPAA-specific recommendations"""
        recommendations = []
        
        if phi_findings:
            recommendations.extend([
                "Implement encryption for PHI at rest and in transit",
                "Add role-based access controls (RBAC) for PHI",
                "Implement comprehensive audit logging",
                "Add automatic session timeout",
                "Implement data backup and disaster recovery"
            ])
        
        return recommendations
    
    def export_report(self, report: dict[str, Any], output_path: str):
        """
        Export compliance report to JSON file.
        
        Args:
            report: Compliance report dict
            output_path: Path to save the report
        """
        try:
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Compliance report exported to {output_path}")
        except Exception as e:
            logger.error(f"Failed to export report: {str(e)}")


def generate_compliance_report(
    scan_results: list[dict[str, Any]],
    project_name: str,
    report_type: str = "SOC2"
) -> dict[str, Any]:
    """
    Convenience function to generate compliance report.
    
    Args:
        scan_results: List of security findings
        project_name: Name of the project
        report_type: Type of report (SOC2, GDPR, HIPAA)
        
    Returns:
        Compliance report dict
    """
    reporter = ComplianceReporter()
    
    if report_type.upper() == "SOC2":
        return reporter.generate_soc2_report(scan_results, project_name)
    elif report_type.upper() == "GDPR":
        return reporter.generate_gdpr_report(scan_results, project_name)
    elif report_type.upper() == "HIPAA":
        return reporter.generate_hipaa_report(scan_results, project_name)
    else:
        raise ValueError(f"Unknown report type: {report_type}")
