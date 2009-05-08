#!/usr/bin/env python

import os
import re
import string
from flup.server.fcgi import WSGIServer

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

def render_tpl(template, args=None):
    html = open('var/templates/%s.html' % template).read()
    out = string.Template(html)
    return out.substitute(args)

def render_blurb(blurb, args=None):
    html = open('var/blurbs/%s/blurb.html' % blurb).read()
    if args is None:
        return html
    else:
        out = string.Template(html)
        return out.substitute(args)

def static(environ, start_response, args):
    args['CONTENT'] = render_blurb(args['CONTENT_BLURB'])
    ok200(start_response)
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

    # change to root of project
    # __file__ is like /var/.../dispatch.fcgi
    os.chdir(__file__.rsplit('/', 2)[0])


    map = [ \
           (r'/',       static, {'PAGE_TITLE': 'ongardie.net', 'CONTENT_BLURB': 'home'}),
           (r'/diego/', static, {'PAGE_TITLE': 'ongardie.net', 'CONTENT_BLURB': 'diego'}),
          ]

    ret = find_controller(map, environ['PATH_INFO'])
    if ret is not None:
        (controller, controller_args) = ret
        controller_args['VAR_URL_PREFIX'] = '/var'
        return controller(environ, start_response, controller_args)
    else:
        return err404(start_response)

if __name__ == '__main__':
    WSGIServer(www_app).run()

# vim: et sw=4 ts=4:
