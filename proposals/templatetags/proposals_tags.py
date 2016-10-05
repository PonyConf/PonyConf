from django import template

from proposals.utils import markdown_to_html


register = template.Library()


@register.simple_tag
def markdown(value):
    return markdown_to_html(value)

@register.filter('duration_format')
def duration_format(value):
    value = int(value)
    hours = int(value/60)
    minutes = value%60
    return '%d h %02d' % (hours, minutes)
