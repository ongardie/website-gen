#!/usr/bin/env python

from flup.server.fcgi import WSGIServer

def test_app(environ, start_response):
       start_response('200 OK', [('Content-Type', 'text/html')])
       return 'Hello World!\n'

if __name__ == '__main__':
    WSGIServer(test_app).run()
