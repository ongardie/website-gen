# Copyright (c) 2009, Diego Ongaro <ongardie@gmail.com>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

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
    if 'tags' in vars:
        vars['tags'] = vars['tags'].split()
    else:
        vars['tags'] = []
    vars.update(args)
    try:
        vars['blurb'] = render_file('var/blog/%s/blurb.html' % args['slug'], vars)
    except IOError:
        return start_response.err404()
    args['PAGE_TITLE'] = vars['title']
    args['CONTENT'] = render_tpl('blog/one', vars)

    # update page trail
    environ['trail'].add(args['PAGE_TITLE'])
    args['trail'] = environ['trail']

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
    start_response('200 OK', [('Content-Type', 'text/xml; charset="utf-8"')])
    return rss.to_xml(encoding='utf-8')

def index(environ, start_response, args):
    import os

    index = read_index()

    articles = []
    for (slug, vars) in index.items():
        vars['slug'] = slug
        vars['thumb'] = os.path.exists('var/blog/%s/thumb.jpg' % slug)

        if 'tags' in vars:
            vars['tags'] = vars['tags'].split()
        else:
            vars['tags'] = []

        if 'tag' in args and args['tag'] not in vars['tags']:
                continue

        blurb_args = vars.copy()
        blurb_args.update(args)
        try:
            vars['blurb'] = render_file('var/blog/%s/blurb.html' % slug, blurb_args)
        except IOError:
            continue

        articles.append(vars)

    if 'tag' in args:
        args['PAGE_TITLE'] = 'Blog: %s Tag' % args['tag']
    else:
        args['PAGE_TITLE'] = 'Blog Index'
    args['articles'] = articles
    args['CONTENT'] = render_tpl('blog/index', args)

    # update page trail
    environ['trail'].add(args['PAGE_TITLE'])
    args['trail'] = environ['trail']

    start_response.ok200()
    return render_tpl('base', args)
