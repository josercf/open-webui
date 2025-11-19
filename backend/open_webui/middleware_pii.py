"""
PII (Personally Identifiable Information) Filter Middleware
Protege contra envio de dados sensíveis de pacientes
"""

import re
import json
import logging
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class PIICategory(Enum):
    """Categories of Personally Identifiable Information"""
    CPF = "cpf"  # Brazilian ID
    EMAIL = "email"
    PHONE = "phone"
    CREDIT_CARD = "credit_card"
    SSN = "ssn"  # Social Security Number
    PASSPORT = "passport"
    MEDICAL_RECORD = "medical_record"
    PATIENT_NAME = "patient_name"
    ADDRESS = "address"
    DATE_OF_BIRTH = "date_of_birth"
    INSURANCE_ID = "insurance_id"
    BANK_ACCOUNT = "bank_account"
    IP_ADDRESS = "ip_address"


class PIIDetectionResult:
    """Result of PII detection"""
    def __init__(self):
        self.found_pii: Dict[PIICategory, List[str]] = {}
        self.is_safe: bool = True
        self.risk_level: str = "low"  # low, medium, high
        self.message: str = ""

    def add_pii(self, category: PIICategory, values: List[str]):
        """Add detected PII"""
        if category not in self.found_pii:
            self.found_pii[category] = []
        self.found_pii[category].extend(values)
        self.is_safe = False

    def to_dict(self) -> Dict:
        """Convert to dict"""
        return {
            "is_safe": self.is_safe,
            "found_pii": {k.value: v for k, v in self.found_pii.items()},
            "risk_level": self.risk_level,
            "message": self.message
        }


class PIIFilter:
    """
    Filter for detecting and protecting against PII exposure
    """

    # PII Patterns
    PATTERNS = {
        PIICategory.CPF: r'\d{3}\.\d{3}\.\d{3}-\d{2}|\d{11}',  # CPF format
        PIICategory.EMAIL: r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        PIICategory.PHONE: r'\(?(\d{2})\)?\s?9?\d{4}-?\d{4}|\+55\s?\d{2}\s?\d{4,5}-?\d{4}',
        PIICategory.CREDIT_CARD: r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
        PIICategory.SSN: r'\d{3}-\d{2}-\d{4}',
        PIICategory.PASSPORT: r'[A-Z]{2}\d{6,9}',
        PIICategory.MEDICAL_RECORD: r'(MRN|record number|prontuário)[\s:]*\d+',
        PIICategory.ADDRESS: r'\d+\s+[\w\s]+(?:street|avenue|road|st|ave|rd|rua|avenida)',
        PIICategory.DATE_OF_BIRTH: r'\d{2}[/-]\d{2}[/-]\d{4}|\d{4}[/-]\d{2}[/-]\d{2}',
        PIICategory.INSURANCE_ID: r'(insurance|apólice)[\s:]*[A-Z0-9]{6,}',
        PIICategory.BANK_ACCOUNT: r'(account|conta)[\s:]*\d{8,17}',
        PIICategory.IP_ADDRESS: r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
    }

    # Sensitive keywords that indicate patient data
    SENSITIVE_KEYWORDS = [
        'paciente', 'patient', 'nome', 'name', 'data de nascimento',
        'date of birth', 'endereço', 'address', 'telefone', 'phone',
        'CPF', 'RG', 'prontuário', 'medical record', 'histórico médico',
        'medical history', 'diagnóstico', 'diagnosis', 'tratamento',
        'treatment', 'medicação', 'medication', 'alergia', 'allergy'
    ]

    def __init__(self, strict_mode: bool = True):
        """
        Initialize PII Filter

        Args:
            strict_mode: If True, block any query with PII. If False, just warn
        """
        self.strict_mode = strict_mode
        self.compiled_patterns = {
            category: re.compile(pattern, re.IGNORECASE)
            for category, pattern in self.PATTERNS.items()
        }

    def detect_pii(self, text: str) -> PIIDetectionResult:
        """
        Detect PII in text

        Args:
            text: Text to scan

        Returns:
            PIIDetectionResult with findings
        """
        result = PIIDetectionResult()

        if not text:
            return result

        # Check for PII patterns
        for category, pattern in self.compiled_patterns.items():
            matches = pattern.findall(text)
            if matches:
                result.add_pii(category, matches)
                logger.warning(f"Detected {category.value} in query: {len(matches)} matches")

        # Determine risk level
        if len(result.found_pii) == 0:
            result.risk_level = "low"
            result.message = "No PII detected"
        elif len(result.found_pii) == 1:
            result.risk_level = "medium"
            result.message = "Single PII type detected"
        else:
            result.risk_level = "high"
            result.message = "Multiple PII types detected"

        return result

    def sanitize_query(self, text: str) -> str:
        """
        Remove/mask PII from query

        Args:
            text: Query text to sanitize

        Returns:
            Sanitized text with PII masked
        """
        sanitized = text

        for category, pattern in self.compiled_patterns.items():
            if category == PIICategory.CPF:
                sanitized = pattern.sub("[CPF REMOVED]", sanitized)
            elif category == PIICategory.EMAIL:
                sanitized = pattern.sub("[EMAIL REMOVED]", sanitized)
            elif category == PIICategory.PHONE:
                sanitized = pattern.sub("[PHONE REMOVED]", sanitized)
            elif category == PIICategory.CREDIT_CARD:
                sanitized = pattern.sub("[CARD REMOVED]", sanitized)
            elif category == PIICategory.PATIENT_NAME:
                sanitized = pattern.sub("[NAME REMOVED]", sanitized)
            elif category == PIICategory.ADDRESS:
                sanitized = pattern.sub("[ADDRESS REMOVED]", sanitized)
            elif category == PIICategory.MEDICAL_RECORD:
                sanitized = pattern.sub("[MRN REMOVED]", sanitized)
            else:
                sanitized = pattern.sub(f"[{category.value.upper()} REMOVED]", sanitized)

        return sanitized

    def validate_query(self, query: str) -> Tuple[bool, str, PIIDetectionResult]:
        """
        Validate query for PII exposure

        Args:
            query: Query text to validate

        Returns:
            Tuple of (is_valid, message, result)
        """
        result = self.detect_pii(query)

        if result.is_safe:
            return True, "Query is safe - no PII detected", result

        if self.strict_mode:
            message = f"BLOCKED: {result.message}. Detected: {', '.join(pii.value for pii in result.found_pii.keys())}"
            return False, message, result
        else:
            message = f"WARNING: {result.message}. Detected: {', '.join(pii.value for pii in result.found_pii.keys())}"
            return True, message, result

    def check_patient_context(self, text: str) -> bool:
        """
        Check if query appears to contain patient-specific information

        Args:
            text: Text to check

        Returns:
            True if patient context detected
        """
        text_lower = text.lower()

        for keyword in self.SENSITIVE_KEYWORDS:
            if keyword in text_lower:
                return True

        return False

    def create_filter_report(self, query: str, result: PIIDetectionResult) -> Dict[str, Any]:
        """
        Create detailed filter report

        Args:
            query: Original query
            result: Detection result

        Returns:
            Detailed report
        """
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "query_length": len(query),
            "is_safe": result.is_safe,
            "risk_level": result.risk_level,
            "detected_pii_types": list(result.found_pii.keys()),
            "detected_pii_count": sum(len(v) for v in result.found_pii.values()),
            "message": result.message,
            "patient_context_detected": self.check_patient_context(query)
        }


def detect_patient_data_leak(query: str) -> Tuple[bool, List[str], str]:
    """
    Quick function to detect patient data leaks

    Args:
        query: Query to check

    Returns:
        Tuple of (is_safe, leaked_data_types, reason)
    """
    pii_filter = PIIFilter(strict_mode=True)
    result = pii_filter.detect_pii(query)

    if result.is_safe:
        return True, [], "No patient data detected"

    leaked_types = [pii.value for pii in result.found_pii.keys()]
    return False, leaked_types, result.message


# Example usage
if __name__ == "__main__":
    pii_filter = PIIFilter(strict_mode=True)

    # Test cases
    test_queries = [
        "Paciente João Silva, CPF 123.456.789-10, nascido em 15/05/1980",
        "Pesquisa sobre COVID-19 em pacientes idosos",
        "Email: patient@example.com, telefone (11) 98765-4321",
        "Qual é o tratamento mais recente para diabetes?"
    ]

    for query in test_queries:
        is_valid, message, result = pii_filter.validate_query(query)
        print(f"\nQuery: {query}")
        print(f"Valid: {is_valid}")
        print(f"Message: {message}")
        print(f"Details: {result.to_dict()}")
