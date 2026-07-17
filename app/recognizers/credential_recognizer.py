from presidio_analyzer import Pattern, PatternRecognizer


class CredentialRecognizer(PatternRecognizer):
   #we are using presidio-analyzer to detect credentials in text. This class defines a custom recognizer for credentials such as passwords, API keys, and tokens.

    def __init__(self):#it is constructing a list of patterns that represent different types of credentials. Each pattern has a name, a regular expression to match the credential, and a score indicating the confidence level of the match.
        patterns = [#?i ignore case sensitivity in regex, \smeans zero or more spaces, \S means any non-whitespace character, + means one or more occurrences of the preceding element, and {10,} means at least 10 occurrences of the preceding element.
            Pattern(
                name="password_pattern",
                regex=r"(?i)\b(password|pwd|passwd)\b\s*(?:is|are|was|were|[:=]|\s)\s*['\"]?[^\s'\",}]+['\"]?",
                score=0.9,
            ),
            Pattern(
                name="api_key_pattern",
                regex=r"(?i)\b(api[_-]?key|apikey)\b\s*(?:is|are|was|were|[:=]|\s)\s*['\"]?[^\s'\",}]+['\"]?",
                score=0.9,
            ),
            Pattern(
                name="secret_token_pattern",
                regex=r"(?i)\b(secret|token|access[_-]?key)\b\s*(?:is|are|was|were|[:=]|\s)\s*['\"]?[^\s'\",}]+['\"]?",
                score=0.85,
            ),
            Pattern(
                name="bearer_token_pattern",#detects bearer tokens, which are often used in authentication headers for APIs. The regex matches the word "bearer" followed by one or more spaces and then a string of alphanumeric characters, hyphens, underscores, or periods that is at least 10 characters long.
                regex=r"(?i)bearer\s+[a-z0-9\-_\.]{10,}",
                score=0.9,
            ),
            Pattern(
                name="aws_access_key_pattern",
                regex=r"AKIA[0-9A-Z]{16}",
                score=0.95,
            ),
            Pattern(
                name="common_key_prefixes",#catches vendor keys even without a labeled prefix like "key=" - OpenAI (sk-), Stripe (pk_), GitHub (ghp_), Slack (xoxb-/xoxp-/xoxa-/xoxr-/xoxs-), Google API (AIza)
                regex=r"\b(sk-|pk_|ghp_|xox[baprs]-|AIza)[a-zA-Z0-9\-_]{10,}\b",
                score=0.9,
            ),
        ]
        super().__init__(
            supported_entity="CREDENTIAL",
            patterns=patterns,
            context=["password", "secret", "key", "token", "credential"],
        )