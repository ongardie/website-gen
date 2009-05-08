#!/usr/bin/env python

import re
from flup.server.fcgi import WSGIServer

def test_app(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/html')])
    return 'Hello World!\n'

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

    map = [(r'/', test_app)]

    ret = find_controller(map, environ['PATH_INFO'])
    if ret:
        (controller, controller_args) = ret
        return controller(environ, start_response, **controller_args)
    else:
        start_response('404 Not Found', [('Content-Type', 'text/html')])
        return '<h1>404 Not Found</h1>'

if __name__ == '__main__':
    WSGIServer(www_app).run()

# vim: et sw=4 ts=4:
