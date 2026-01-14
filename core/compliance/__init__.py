"""
Compliance module for regulatory requirements.

Provides audit logging and compliance query capabilities for:
- SEC (Securities and Exchange Commission)
- FINRA (Financial Industry Regulatory Authority)
- MiFID II (Markets in Financial Instruments Directive)
- GDPR (General Data Protection Regulation)
- CCPA (California Consumer Privacy Act)
"""

from core.compliance.audit_logger import AuditLogger

__all__ = ["AuditLogger"]
