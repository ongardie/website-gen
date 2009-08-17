#!/usr/bin/env python

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

import os
import re
from flup.server.fcgi import WSGIServer
from beaker.middleware import SessionMiddleware
from configobj import ConfigObj

from trail import TrailMiddleware
from template import render_file, render_tpl, render_blurb

def get_site_config():
    global _config
    try:
        return _config
    except NameError:
        _config = ConfigObj('src/config.ini',
                            list_values=False, file_error=True)
        controller = _config['controller']
        controller['FULL_URL_PREFIX']     = controller['URL_TILL_PATH'] + controller['SHORT_URL_PREFIX']
        controller['FULL_VAR_URL_PREFIX'] = controller['URL_TILL_PATH'] + controller['SHORT_VAR_URL_PREFIX']
        controller['URL_PREFIX']          = controller['SHORT_URL_PREFIX']
        controller['VAR_URL_PREFIX']      = controller['SHORT_VAR_URL_PREFIX']
        return _config

def get_base_controller_args():
    return get_site_config()['controller'].copy()

def err404(start_response):
    start_response('404 Not Found', [('Content-Type', 'text/html')])

    args = get_base_controller_args()
    args['PAGE_TITLE'] = '404 - Not Found'
    try:
        args['CONTENT'] = render_blurb('404')
    except IOError:
        args['CONTENT'] = 'Page not found.'
    return render_tpl('base', args)

def ok200(start_response):
    start_response('200 OK', [('Content-Type', 'text/html')])

def static(environ, start_response, args):
    try:
        args['CONTENT'] = render_blurb(args['CONTENT_BLURB'],
                                       get_base_controller_args())
    except IOError:
        return start_response.err404()

    # update page trail
    environ['trail'].add(args['PAGE_TITLE'])
    args['trail'] = environ['trail']

    start_response.ok200()
    return render_tpl('base', args)

def find_controller(map, url_prefix, path):

    if not path.startswith(url_prefix):
        return None
    path = path[len(url_prefix):]

    for line in map:
        pattern = line[0]
        controller = line[1]
        if len(line) == 3:
            controller_args = line[2]
        else:
            controller_args = {}

        match = re.search('^%s$' % pattern, path)
        if match is not None:

            # add in any matched groups (highest priority)
            groups = match.groupdict()
            for k in groups:
                if groups[k] != '':
                    controller_args[k] = groups[k]

            return (controller, controller_args)

    return None

def www_app(environ, start_response):

    config = get_site_config()

    start_response.err404 = lambda: err404(start_response)
    start_response.ok200  = lambda: ok200(start_response)

    map = [ \
           (r'/blog/?',  'blog.index'),
           (r'/blog/\+(?P<tag>[\w-]{1,99})/?', 'blog.index'),
           (r'/blog/(?P<slug>[\w-]{1,99})/?', 'blog.article'),
           (r'/blog/\+(?P<tag>[\w-]{1,99})/rss.xml', 'blog.rss'),
           (r'/blog/rss.xml', 'blog.rss'),
          ]

    try:
        staticpages = ConfigObj('var/staticpages.ini',
                                list_values=True, file_error=True)
    except IOError:
        staticpages = {}
    for (blurb, vars) in staticpages.items():
        if isinstance(vars['url'], list):
            urls = vars['url']
        else:
            urls = [vars['url']]
        for url in urls:
            map.append((url, static,
                        {'PAGE_TITLE': vars['title'],
                         'CONTENT_BLURB': blurb}))

    ret = find_controller(map, config['controller']['URL_PREFIX'], environ['PATH_INFO'])
    if ret is not None:
        (controller, args) = ret
        controller_args = get_base_controller_args()
        controller_args.update(args)

        if type(controller) == str:
            module_name, controller_name = controller.rsplit('.', 1)
            module = __import__(module_name)
            controller = module.__getattribute__(controller_name)

        out = controller(environ, start_response, controller_args)
        if isinstance(out, str):
            out = [out]
        return out
    else:
        return start_response.err404()

if __name__ == '__main__':

    # change to root of project
    # __file__ is like /file/path/to/src/dispatch.fcgi
    os.chdir(__file__.rsplit('/', 2)[0])

    config = get_site_config()

    wsgi_app = TrailMiddleware(www_app)

    session_opts = {
        'session.type': 'file',
        'session.data_dir': 'data/',
        'session.lock_dir': 'data/lock/',
        'session.key': config['session']['key'],
        'session.cookie_domain': config['session']['cookie_domain'],
    }
    wsgi_app = SessionMiddleware(wsgi_app, session_opts)
    WSGIServer(wsgi_app).run()

# vim: et sw=4 ts=4:
