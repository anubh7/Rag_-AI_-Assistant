from app.services.pii_masking_service import pii_masking_service


def mask_pii(text: str) -> str:
    """Mask PII/credentials in a given text string."""
    if not text:
        return text
    return pii_masking_service.mask_text(text)