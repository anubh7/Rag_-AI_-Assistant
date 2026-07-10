"""
App-wide constant values (kept separate from config/env-driven settings).
"""

STATUS_SUCCESS = "success"
STATUS_ERROR = "error"

# Loader mapping (extension -> loader key), consumed by loader_factory
SUPPORTED_LOADERS = {
    ".pdf": "pdf",
    ".csv": "csv",
    ".xlsx": "excel",
    ".xls": "excel",
    ".docx": "word",
    ".txt": "text",
}

DISTANCE_METRIC = "Cosine"

ROLE_USER = "user"
ROLE_ASSISTANT = "assistant"
ROLE_SYSTEM = "system"

ERR_UNSUPPORTED_FILE = "Unsupported file type."
ERR_FILE_TOO_LARGE = "File exceeds maximum allowed size."
ERR_COLLECTION_NOT_FOUND = "Collection not found."
ERR_NO_DOCS_RETRIEVED = "No relevant documents were found for this query."
