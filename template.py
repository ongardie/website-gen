# Copyright (c) 2009-2020, Diego Ongaro.
# Licensed under the BSD 2-Clause License.

from mako.template import Template
from markdown import markdown


def render_file(file, args):
    body = open(file).read()
    if str(file).endswith('.md'):
        body = markdown(body)
    out = Template(body, strict_undefined=True)
    return out.render(**args)
