from django import template
from base.utils import format_phone_number, extract_digits, get_call_url, get_call_icon

register = template.Library()

@register.filter
def phone_format(value):
    """
    Template filter to format phone numbers nicely.
    Usage: {{ phone_number|phone_format }}
    """
    return format_phone_number(value)

@register.filter
def phone_digits(value):
    """
    Template filter to extract digits from phone numbers.
    Usage: {{ phone_number|phone_digits }}
    """
    return extract_digits(value)

@register.filter
def call_url(value, call_type='PHONE_CALL'):
    """
    Template filter to generate call URL.
    Usage: {{ phone_number|call_url:'WHATSAPP' }}
    """
    return get_call_url(value, call_type)
