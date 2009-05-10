from template import render_file, render_tpl, render_blurb

def read_index():
    from configobj import ConfigObj
    return ConfigObj('var/blog/index.ini', list_values=False)

def article(environ, start_response, args):
    index = read_index()

    try:
        vars = index[args['slug']]
    except KeyError:
        return start_response.err404()
    vars.update(args)
    try:
        vars['blurb'] = render_file('var/blog/%s/blurb.html' % args['slug'], vars)
    except IOError:
        return start_response.err404()
    args['PAGE_TITLE'] = vars['title']
    args['CONTENT'] = render_tpl('blog/one', vars)

    start_response.ok200()
    return render_tpl('base', args)

def rss(environ, start_response, args):

    import PyRSS2Gen
    from datetime import datetime
    from tzinfo_examples import Local

    def datetime_from_localstr(localstr):
        date = datetime.strptime(localstr, '%Y-%m-%d %H:%M')
        date = date - Local.utcoffset(date)
        return date

    index = read_index()

    items = []
    for (slug, vars) in index.items():
        vars.update(args)
        items.append(PyRSS2Gen.RSSItem(
           title = vars['title'],
           link = 'http://ongardie.net/blog/%s/' % slug,
           description = render_file('var/blog/%s/blurb.html' % slug, vars),
           guid = PyRSS2Gen.Guid('http://ongardie.net/blog/%s/' % slug),
           pubDate = datetime_from_localstr(vars['date'])))
    rss = PyRSS2Gen.RSS2(
        title = "ongardie.net",
        link = "http://ongardie.net/blog/",
        description = "ongardie.net Blog",
        lastBuildDate = datetime.now(),
        items = items)
    start_response('200 OK', [('Content-Type', 'text/xml')])
    return rss.to_xml()

def index(environ, start_response, args):
    import os

    index = read_index()

    args['PAGE_TITLE'] = 'Blog Index'

    content = []
    for (slug, vars) in index.items():
        vars['slug'] = slug
        vars['thumb'] = os.path.exists('var/blog/%s/thumb.jpg' % slug)
        vars.update(args)
        content.append(render_tpl('blog/index_one', vars))
    args['CONTENT'] = '\n\n'.join(content)

    start_response.ok200()
    return render_tpl('base', args)
