from presidio_analyzer import Pattern, PatternRecognizer


class CredentialRecognizer(PatternRecognizer):
   #we are using presidio-analyzer to detect credentials in text. This class defines a custom recognizer for credentials such as passwords, API keys, and tokens.

    def __init__(self):#it is constructing a list of patterns that represent different types of credentials. Each pattern has a name, a regular expression to match the credential, and a score indicating the confidence level of the match.
        patterns = [#?i ignore case sensitivity in regex, \smeans zero or more spaces, \S means any non-whitespace character, + means one or more occurrences of the preceding element, and {10,} means at least 10 occurrences of the preceding element.
            Pattern(
                name="password_pattern",
                regex=r"(?i)(password|pwd|passwd)\s*[:=]\s*\S+",
                score=0.9,
            ),
            Pattern(
                name="api_key_pattern",
                regex=r"(?i)(api[_-]?key|apikey)\s*[:=]\s*\S+",
                score=0.9,
            ),
            Pattern(
                name="secret_token_pattern",
                regex=r"(?i)(secret|token|access[_-]?key)\s*[:=]\s*\S+",
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
        ]
        super().__init__(
            supported_entity="CREDENTIAL",
            patterns=patterns,
            context=["password", "secret", "key", "token", "credential"],
        )