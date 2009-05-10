#!/usr/bin/env python

import os
import re
from flup.server.fcgi import WSGIServer
from beaker.middleware import SessionMiddleware

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
    return render_tpl('base', args)

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
           (r'/',       static, {'PAGE_TITLE': 'ongardie.net', 'CONTENT_BLURB': 'home'}),
           (r'/diego/', static, {'PAGE_TITLE': 'ongardie.net', 'CONTENT_BLURB': 'diego'}),
           (r'/blog/',  'blog.index'),
           (r'/blog/(?P<slug>[\w-]{1,99})/', 'blog.article'),
           (r'/blog/rss.xml', 'blog.rss'),
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

    session_opts = {
        'session.type': 'file',
        'session.data_dir': 'data/',
        'session.lock_dir': 'data/lock/',
        'session.key': 'ongardie.net'
    }
    wsgi_app = SessionMiddleware(www_app, session_opts)
    WSGIServer(wsgi_app).run()

# vim: et sw=4 ts=4:
