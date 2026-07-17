from app.services.pii_masking_service import pii_masking_service

sample_text = (
    "Hi, my email is yashagarwal123@gmail.com, phone is +1-202-555-0173, "
    "my credit card is 4111111111111111, bank account number is 123456789012, "
    "IBAN is DE89370400440532013000, IP is 192.168.1.1, SSN is 078-05-1120, "
    "password: SuperSecret123, api_key=sk-abcdef1234567890"
)

masked = pii_masking_service.mask_text(sample_text)
print(masked)