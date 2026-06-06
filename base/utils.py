# ==============================================================================
# UTILITY FUNCTIONS FOR SILVERCONNECT
# ==============================================================================

import re
from django.utils.text import format_lazy

# ==============================================================================
# 1. PHONE NUMBER FORMATTING
# ==============================================================================

def format_phone_number(phone_number):
    """
    Formats phone numbers to a consistent format.
    Handles various input patterns and returns a standardized format.
    
    Examples:
        format_phone_number('5551234567') -> '+1 (555) 123-4567'
        format_phone_number('+1-555-123-4567') -> '+1 (555) 123-4567'
        format_phone_number('555-123-4567') -> '(555) 123-4567'
    """
    if not phone_number:
        return ""
    
    # Remove all non-digit characters except leading +
    cleaned = re.sub(r'[^\d+]', '', str(phone_number))
    
    # Remove leading +1 or +91 etc for processing
    country_code = ""
    if cleaned.startswith('+'):
        parts = re.match(r'(\+\d{1,3})(\d+)', cleaned)
        if parts:
            country_code = parts.group(1)
            cleaned = parts.group(2)
    
    # Format 10-digit number (US/Canada)
    if len(cleaned) == 10:
        formatted = f"({cleaned[:3]}) {cleaned[3:6]}-{cleaned[6:]}"
        if country_code:
            formatted = f"{country_code} {formatted}"
        elif not phone_number.startswith('+'):
            formatted = f"+1 {formatted}"
        return formatted
    
    # Format 11-digit number (US with leading 1)
    elif len(cleaned) == 11 and cleaned.startswith('1'):
        formatted = f"+1 ({cleaned[1:4]}) {cleaned[4:7]}-{cleaned[7:]}"
        return formatted
    
    # Format 10-digit Indian number
    elif len(cleaned) == 10:
        formatted = f"+91 {cleaned[:5]} {cleaned[5:]}"
        return formatted
    
    # Return as-is if we can't format it
    else:
        if country_code:
            return f"{country_code} {cleaned}"
        return phone_number


def extract_digits(phone_number):
    """
    Extracts only digits from a phone number for tel: links.
    
    Examples:
        extract_digits('(555) 123-4567') -> '5551234567'
        extract_digits('+1 (555) 123-4567') -> '+15551234567'
    """
    if not phone_number:
        return ""
    
    # Keep leading + and digits only
    return re.sub(r'[^\d+]', '', str(phone_number))


# ==============================================================================
# 2. CALL TYPE HELPERS
# ==============================================================================

def get_call_url(phone_number, call_type='PHONE_CALL'):
    """
    Generates appropriate URL for different communication methods.
    
    call_type options: 'PHONE_CALL', 'WHATSAPP', 'SMS', 'EMAIL'
    """
    clean_phone = extract_digits(phone_number)
    
    if call_type == 'WHATSAPP':
        # WhatsApp link (works on mobile and web)
        return f"https://wa.me/{clean_phone}?text=Hello"
    elif call_type == 'SMS':
        # SMS link
        return f"sms:{clean_phone}"
    elif call_type == 'PHONE_CALL':
        # Tel link
        return f"tel:{clean_phone}"
    elif call_type == 'EMAIL':
        return None
    
    return None


def get_call_icon(call_type):
    """
    Returns Bootstrap icon class for different call types.
    """
    icons = {
        'PHONE_CALL': 'bi-telephone-fill',
        'WHATSAPP': 'bi-whatsapp',
        'SMS': 'bi-chat-dots-fill',
        'EMAIL': 'bi-envelope-fill',
    }
    return icons.get(call_type, 'bi-telephone-fill')


def get_call_icon_color(call_type):
    """
    Returns Bootstrap color class for different call types.
    """
    colors = {
        'PHONE_CALL': 'success',
        'WHATSAPP': 'success',
        'SMS': 'info',
        'EMAIL': 'primary',
    }
    return colors.get(call_type, 'secondary')
