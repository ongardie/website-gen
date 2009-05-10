#!/usr/bin/env python

import os
import re
from flup.server.fcgi import WSGIServer

from template import render_file, render_tpl, render_blurb

from blog import blog

def err404(start_response):
    start_response('404 Not Found', [('Content-Type', 'text/html')])

    # the following string was stolen from lighttpd output
    return """
<?xml version="1.0" encoding="iso-8859-1"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
         "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
 <head>
  <title>404 - Not Found</title>
 </head>
 <body>
  <h1>404 - Not Found</h1>
 </body>

</html>
"""

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

    # change to root of project
    # __file__ is like /var/.../dispatch.fcgi
    os.chdir(__file__.rsplit('/', 2)[0])

    map = [ \
           (r'/',       static, {'PAGE_TITLE': 'ongardie.net', 'CONTENT_BLURB': 'home'}),
           (r'/diego/', static, {'PAGE_TITLE': 'ongardie.net', 'CONTENT_BLURB': 'diego'}),
           (r'/blog/',  blog),
           (r'/blog/(?P<slug>[\w-]{1,99})/', blog),
           (r'/blog/rss.xml', blog, {'rss': True}),
          ]

    ret = find_controller(map, environ['PATH_INFO'])
    if ret is not None:
        (controller, controller_args) = ret
        controller_args['VAR_URL_PREFIX'] = '/var'
        controller_args['URL_PREFIX'] = ''
        controller_args['GOOGLE_ANALYTICS_ACCOUNT'] = 'UA-8777280-1'
        return controller(environ, start_response, controller_args)
    else:
        return start_response.err404()

if __name__ == '__main__':
    WSGIServer(www_app).run()

# vim: et sw=4 ts=4:
