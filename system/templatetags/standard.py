import datetime
from django import template

register = template.Library()

@register.inclusion_tag('system/action-form.html')
def action_form(text, url, css_class='action-form'):
    return {'text': text, 'url': url, 'css_class': css_class}
