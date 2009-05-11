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
from trail import TrailMiddleware

from template import render_file, render_tpl, render_blurb

def get_base_controller_args():
    from configobj import ConfigObj
    config = ConfigObj('src/config.ini', list_values=False, file_error=True)
    return config['controller']

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
    args['CONTENT'] = render_blurb(args['CONTENT_BLURB'])
    start_response.ok200()
    return render_tpl('base', args, environ)

def find_controller(map, path):
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

    start_response.err404 = lambda: err404(start_response)
    start_response.ok200  = lambda: ok200(start_response)

    map = [ \
           (r'/?',       static, {'PAGE_TITLE': 'ongardie.net', 'CONTENT_BLURB': 'home'}),
           (r'/diego/?', static, {'PAGE_TITLE': 'Diego Ongaro', 'CONTENT_BLURB': 'diego'}),
           (r'/blog/?',  'blog.index'),
           (r'/blog/(?P<slug>[\w-]{1,99})/?', 'blog.article'),
           (r'/blog/rss.xml', 'blog.rss'),
           (r'/misc/?', static, {'PAGE_TITLE': 'Misc', 'CONTENT_BLURB': 'misc'}),
           (r'/misc/movies/?', static, {'PAGE_TITLE': 'Movie Log', 'CONTENT_BLURB': 'movies'}),
          ]

    ret = find_controller(map, environ['PATH_INFO'])
    if ret is not None:
        (controller, args) = ret
        controller_args = get_base_controller_args()
        controller_args.update(args)

        if type(controller) == str:
            module_name, controller_name = controller.rsplit('.', 1)
            module = __import__(module_name)
            controller = module.__getattribute__(controller_name)

        return controller(environ, start_response, controller_args)
    else:
        return start_response.err404()

if __name__ == '__main__':

    # change to root of project
    # __file__ is like /file/path/to/src/dispatch.fcgi
    os.chdir(__file__.rsplit('/', 2)[0])

    wsgi_app = TrailMiddleware(www_app)

    session_opts = {
        'session.type': 'file',
        'session.data_dir': 'data/',
        'session.lock_dir': 'data/lock/',
        'session.key': 'ongardie.net'
    }
    wsgi_app = SessionMiddleware(wsgi_app, session_opts)
    WSGIServer(wsgi_app).run()

# vim: et sw=4 ts=4:
