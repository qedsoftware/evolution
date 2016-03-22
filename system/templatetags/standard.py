from django import template

register = template.Library()


@register.inclusion_tag('system/action-form.html')
def action_form(html_id, text, url, css_class='action-form'):
    return {'id': html_id, 'text': text, 'url': url, 'css_class': css_class}
