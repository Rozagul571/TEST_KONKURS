# django_app/core/templatetags/admin_tags.py
"""
Admin uchun template taglar - badge, button, status icon
"""
from django import template
from django.utils.html import format_html

register = template.Library()


# --- Umumiy ranglar  ---
BADGE_COLORS = {
    'success': 'bg-green-100 text-green-800',
    'warning': 'bg-yellow-100 text-yellow-800',
    'danger': 'bg-red-100 text-red-800',
    'info': 'bg-blue-100 text-blue-800',
    'secondary': 'bg-gray-100 text-gray-800',
}

BUTTON_COLORS = {
    'primary': 'bg-blue-600 hover:bg-blue-700',
    'success': 'bg-green-600 hover:bg-green-700',
    'warning': 'bg-yellow-600 hover:bg-yellow-700',
    'danger': 'bg-red-600 hover:bg-red-700',
}

STATUS_ICON_MAP = {
    'active': ('🟢', 'text-green-600'),
    'pending': ('🟡', 'text-yellow-600'),
    'draft': ('⚪', 'text-gray-600'),
    'finished': ('🔵', 'text-blue-600'),
    'canceled': ('🔴', 'text-red-600'),
}


@register.simple_tag
def badge(color: str, text: str) -> str:
    """Badge ko‘rsatish"""
    css_class = BADGE_COLORS.get(color, BADGE_COLORS['secondary'])
    return format_html(
        '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {}">{}</span>',
        css_class, text
    )


@register.simple_tag
def button(color: str, text: str, url: str | None = None, disabled: bool = False) -> str:
    """Admin UI uchun button yaratish"""
    css_class = BUTTON_COLORS.get(color, BUTTON_COLORS['primary'])

    # Disabled button style
    if disabled:
        css_class = 'bg-gray-300 cursor-not-allowed'

    if url and not disabled:
        return format_html(
            '<a href="{}" class="inline-flex items-center px-3 py-1.5 border border-transparent '
            'text-xs font-medium rounded text-white {}">{}</a>',
            url, css_class, text
        )

    return format_html(
        '<button class="inline-flex items-center px-3 py-1.5 border border-transparent '
        'text-xs font-medium rounded text-white {}" {}>{}</button>',
        css_class,
        'disabled="disabled"' if disabled else '',
        text
    )


@register.simple_tag
def status_icon(status: str, label: str) -> str:
    """Statusga mos icon + rang qaytarish"""
    icon, color = STATUS_ICON_MAP.get(status, ('⚪', 'text-gray-600'))

    return format_html(
        '<span class="inline-flex items-center {}"><span class="mr-1">{}</span> {}</span>',
        color, icon, label
    )
