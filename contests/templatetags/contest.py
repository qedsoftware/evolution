from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.inclusion_tag('contests/submission_result.html')
def submission_result(submission, contest_context, html_tag='div',
                      additional_css_classes="", with_helptext=False):
    text = {
        'score': "Score: <strong>%s</strong>" % submission.submission.score,
        'waiting': "Waiting for score...",
        'rejected': "Rejected",
        'accepted': "Accepted",
        'error': "Grading Error",
    }
    css_class = {
        'score': 'score-result',
        'waiting': 'waiting-result',
        'rejected': 'rejected-result',
        'accepted': 'accepted-result',
        'error': 'error-result'
    }
    helptext = {
        'rejected': "There is something wrong with your submission.",
        'accepted': "Exact score is not available at this point.",
        'error': "Don't worry. We'll take care of that."
    }
    result = contest_context.visible_submission_result(submission)
    base_classes = css_class.get(result, 'strange-result')
    classes = ' '.join(['submission-result', base_classes,
        additional_css_classes])
    displayed_helptext = ''
    if with_helptext:
        displayed_helptext = helptext.get(result)
    return {
        'html_tag': html_tag,
        'classes': classes,
        'text': mark_safe(text[result]),
        'helptext': displayed_helptext
    }


@register.simple_tag
def stage_name(stage, contest_context):
    return contest_context.stage_names[stage.id]


@register.simple_tag
def submission_selection_state_icon(submission):
    icon = ""
    if submission.stage.requires_selection:
        if submission.selected:
            icon = '<i class="material-icons selected-icon">grade</i>'
        else:
            icon = '<i class="material-icons not-selected-icon">clear</i>'
    return mark_safe(icon)
