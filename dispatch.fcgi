#!/usr/bin/env python

import os
import re
import string
from flup.server.fcgi import WSGIServer

def test_app(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/html')])
    return 'Hello World!\n'

def home(environ, start_response):
    environ['PAGE_TITLE'] = 'ongardie.net'
    environ['CONTENT'] = 'Hello World'
    start_response('200 OK', [('Content-Type', 'text/html')])
    out = string.Template(open('var/templates/base.html').read())
    return out.substitute(environ)


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

    # change to root of project
    # __file__ is like /var/.../dispatch.fcgi
    os.chdir(__file__.rsplit('/', 2)[0])

    environ['VAR_URL_PREFIX'] = '/var'

    map = [(r'/', home)]

    ret = find_controller(map, environ['PATH_INFO'])
    if ret is not None:
        (controller, controller_args) = ret
        environ.update(controller_args)
        return controller(environ, start_response)
    else:
        start_response('404 Not Found', [('Content-Type', 'text/html')])
        return '<h1>404 Not Found</h1>'

if __name__ == '__main__':
    WSGIServer(www_app).run()

# vim: et sw=4 ts=4:
