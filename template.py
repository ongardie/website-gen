# Copyright (c) 2009-2020, Diego Ongaro.
# Licensed under the BSD 2-Clause License.

from mako.template import Template
from markdown import markdown
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.codehilite import CodeHiliteExtension


def render_file(file, args):
    body = open(file).read()
    if str(file).endswith('.md'):
        body = markdown(body, extensions=[
            CodeHiliteExtension(
                guess_lang=False,
                linenums=False,
                noclasses=True,
            ),
            FencedCodeExtension(),
        ])
    out = Template(body, strict_undefined=True)
    return out.render(**args)
