import markdown
import bleach


MARKDOWN_ALLOWED_TAGS = [
    'a',
    'abbr',
    'acronym',
    'b',
    'br',
    'blockquote',
    'code',
    'div',
    'em',
    'i',
    'li',
    'ol',
    'pre',
    'span',
    'strong',
    'ul',
    'p',
    'table',
    'thead',
    'tr',
    'th',
    'td',
    'tbody',
    'tfoot',
    'h1',
    'h2',
    'h3',
    'h4',
    'h5',
    'h6'
    # 'blockquote', # TODO support in css
    #  definition lists - TODO support them in css
    # 'dl',
    # 'dt',
    # 'dd'
]


ALLOWED_CSS_CLASSES = ['highlight', 'bp', 'c', 'c1', 'cm', 'cp', 'cs', 'err',
     'gd', 'ge', 'gh', 'gi', 'go', 'gp', 'gr', 'gs', 'gt', 'gu', 'hll', 'il',
      'k', 'kc', 'kd', 'kn', 'kp', 'kr', 'kt', 'm', 'mf', 'mh', 'mi', 'mo',
      'na', 'nb', 'nc', 'nd', 'ne', 'nf', 'ni', 'nl', 'nn', 'no', 'nt', 'nv',
      'o', 'ow', 's', 's1', 's2', 'sb', 'sc', 'sd', 'se', 'sh', 'si', 'sr',
      'ss', 'sx', 'vc', 'vg', 'vi', 'w']


def safe_class(tag, name, value):
    return name == "class" and value in ALLOWED_CSS_CLASSES


MARKDOWN_ALLOWED_ATTRIBUTES = {
    'abbr': ['title'],
    'acronym': ['title'],
    'a': ['href', 'title'],
    'span': safe_class,
    'div': safe_class,
    'tr': ['align'],
    'th': ['align'],
    'td': ['align'],
    'tbody': ['align'],
    'tfoot': ['align']
}


def markdown_to_html(source):
    markdown_html = markdown.markdown(source, extensions=['mdx_partial_gfm'])
    return bleach.clean(markdown_html,
        tags=MARKDOWN_ALLOWED_TAGS,
        attributes=MARKDOWN_ALLOWED_ATTRIBUTES)
