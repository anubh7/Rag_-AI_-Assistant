import os

try:
    from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
    from presidio_anonymizer import AnonymizerEngine
    from presidio_anonymizer.entities import OperatorConfig
except ImportError:  # pragma: no cover
    # Fallback stub implementations when Presidio is not installed.
    AnalyzerEngine = None
    Pattern = None
    PatternRecognizer = object
    AnonymizerEngine = None
    class OperatorConfig:  # type: ignore
        def __init__(self, *args, **kwargs):
            pass

from app.recognizers.credential_recognizer import CredentialRecognizer


class BankAccountRecognizer(PatternRecognizer):
    #detects generic bank account numbers (9-18 digits). Indian account numbers
    #don't follow one fixed format, so this is a loose numeric pattern boosted
    #by context words like "account"/"a/c" nearby, since a bare 9-18 digit
    #number alone is too ambiguous (could be a phone number, ID, etc).

    def __init__(self):
        patterns = [
            Pattern(
                name="bank_account_pattern",
                regex=r"\b\d{9,18}\b",
                score=0.5,  # low confidence alone, context boosts this
            ),
        ]
        super().__init__(
            supported_entity="BANK_ACCOUNT_NUMBER",
            patterns=patterns,
            context=["account", "a/c", "acc no", "bank account", "account number"],
        )


class PiiMaskingService:
    def __init__(self):
        self.analyzer = None
        self.anonymizer = None

        # Loading Presidio's NLP engine can trigger a large spaCy model download.
        # Keep local startup lightweight unless explicitly enabled in .env.
        presidio_enabled = os.getenv("PRESIDIO_ENABLED", "false").lower() == "true"

        if AnalyzerEngine is None or not presidio_enabled:
            # Dummy implementations when Presidio is unavailable
            class _DummyRegistry:
                def add_recognizer(self, *args, **kwargs):
                    pass

            class _DummyAnalyzer:
                def __init__(self):
                    self.registry = _DummyRegistry()

                def analyze(self, *args, **kwargs):
                    return []

            class _DummyAnonymizer:
                def anonymize(self, *args, **kwargs):
                    # Return original text unchanged
                    return type("Anon", (), {"text": args[0] if args else ""})()

            self.analyzer = _DummyAnalyzer()
            self.anonymizer = _DummyAnonymizer()
        else:
            try:
                # Presidio may attempt to load/download a spaCy model. Never let
                # optional model setup prevent the API from starting locally.
                self.analyzer = AnalyzerEngine()
                self.analyzer.registry.add_recognizer(CredentialRecognizer())
                self.analyzer.registry.add_recognizer(BankAccountRecognizer())
                self.anonymizer = AnonymizerEngine()
            except Exception as exc:
                print(f"PII analyzer unavailable; using fallback masking mode: {exc}")

                class _FallbackAnalyzer:
                    def analyze(self, *args, **kwargs):
                        return []

                class _FallbackAnonymizer:
                    def anonymize(self, *args, **kwargs):
                        return type("Anon", (), {"text": args[0] if args else ""})()

                self.analyzer = _FallbackAnalyzer()
                self.anonymizer = _FallbackAnonymizer()

        # entities you want detected/masked
        self.entities = [
            "CREDENTIAL",
            "EMAIL_ADDRESS",
            "PHONE_NUMBER",
            "CREDIT_CARD",
            "US_SSN",#social security number
            "IP_ADDRESS",
            "IBAN_CODE",#bank account number (European format only)
            "BANK_ACCOUNT_NUMBER",#custom recognizer for generic/Indian account numbers
        ]

        # every entity masks with *** matching full length, no [REDACTED] tags
        self._full_mask = OperatorConfig(
            "mask", {"masking_char": "*", "chars_to_mask": 999, "from_end": False}
        )

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
                "DEFAULT": self._full_mask,
                "CREDENTIAL": self._full_mask,
                "BANK_ACCOUNT_NUMBER": self._full_mask,
            },
        )
        return anonymized.text

    def contains_pii(self, text: str) -> bool:#this function checks if the input text contains any personally identifiable information (PII) by analyzing it with the Presidio Analyzer. It returns True if any PII is detected, and False otherwise.
        results = self.analyzer.analyze(text=text, entities=self.entities, language="en")
        return len(results) > 0
    
pii_masking_service = PiiMaskingService()# Singleton instance - loaded once, reused across all requests