# django_app/core/templatetags/admin_custom_tags.py
from django import template

register = template.Library()

@register.filter
def get_display(value, choices):
    """status|get_display:CompetitionStatus.choices - 'Active' chiqaradi."""
    for code, display in choices:
        if code == value:
            return display
    return value