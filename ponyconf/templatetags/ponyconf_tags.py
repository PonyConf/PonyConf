from django import template

from ponyconf.utils import markdown_to_html


register = template.Library()


@register.simple_tag
def markdown(value):
    return markdown_to_html(value)
