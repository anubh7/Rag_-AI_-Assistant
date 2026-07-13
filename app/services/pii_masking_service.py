from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig#this is for custom rcognizer i created without these python does not know what to do with the custom recognizer i created

from app.recognizers.credential_recognizer import CredentialRecognizer


class PiiMaskingService:
    def __init__(self):
        self.analyzer = AnalyzerEngine()
        self.analyzer.registry.add_recognizer(CredentialRecognizer())
        self.anonymizer = AnonymizerEngine()

        # entities you want detected/masked
        self.entities = [
            "CREDENTIAL",
            "EMAIL_ADDRESS",
            "PHONE_NUMBER",
            "CREDIT_CARD",
            "US_SSN",#social security number
            "IP_ADDRESS",
            "IBAN_CODE",#bank account number
        ]

    def mask_text(self, text: str) -> str:
        if not text or not text.strip():#if text is empty or only contains whitespace, return the original text without any modifications.
            return text

        results = self.analyzer.analyze(
            text=text,
            entities=self.entities,
            language="en",
        )

        if not results:#if nothing detected, return the original text without any modifications.
            return text

        anonymized = self.anonymizer.anonymize(
            text=text,
            analyzer_results=results,
            operators={
                "DEFAULT": OperatorConfig("replace", {"new_value": "[REDACTED]"}),
                "CREDENTIAL": OperatorConfig("replace", {"new_value": "[REDACTED_CREDENTIAL]"}),
            },
        )
        return anonymized.text

    def contains_pii(self, text: str) -> bool:#this function checks if the input text contains any personally identifiable information (PII) by analyzing it with the Presidio Analyzer. It returns True if any PII is detected, and False otherwise.
        results = self.analyzer.analyze(text=text, entities=self.entities, language="en")
        return len(results) > 0
    
pii_masking_service = PiiMaskingService()# Singleton instance - loaded once, reused across all requests