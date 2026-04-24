from django import template
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag(takes_context=True)
def editable(context, key, default=''):
    """
    Renders stored content for `key`, or `default` if none saved yet.
    For staff users it wraps the text in a span with data-editable attributes
    so the frontend editor can make it clickable and saveable.
    """
    from conference.models import ContentBlock

    try:
        content = ContentBlock.objects.get(key=key).content
    except ContentBlock.DoesNotExist:
        content = default

    request = context.get('request')
    if request and request.user.is_authenticated and request.user.is_staff:
        safe_key = key.replace('"', '&quot;')
        safe_content = content  # content may include HTML; trust DB
        return mark_safe(
            f'<span class="editable-block" data-editable-key="{safe_key}">'
            f'{safe_content}'
            f'</span>'
        )

    return mark_safe(content)
