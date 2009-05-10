from mako.template import Template

def render_file(file, args=None):
    html = open(file).read()
    if args is None:
        return html
    else:
        out = Template(html)
        return out.render(**args)

def render_tpl(template, args=None, environ=None):
    if template == 'base' and environ:
        environ['trail'].add(args['PAGE_TITLE'])
        args['trail'] = environ['trail']
    return render_file('var/templates/%s.html' % template, args)

def render_blurb(blurb, args=None):
    return render_file('var/blurbs/%s/blurb.html' % blurb, args)
