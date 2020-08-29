# Copyright (c) 2009-2020, Diego Ongaro.
# Licensed under the BSD 2-Clause License.

from mako.template import Template
from markdown import markdown
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.codehilite import CodeHiliteExtension
import re


# A line starting with a '##' is a comment in Mako and a header in Markdown.
# We want Markdown's meaning,
def md_preprocessor(input):
    output = []
    for line in input.split('\n'):
        m = re.match(r'^[\t ]*(#{2,6}) (.*)$', line)
        if m is None:
            output.append(line)
        else:
            size = str(len(m.group(1)))
            output.append(f'<h{size}>{m.group(2)}</h{size}>')
    return '\n'.join(output)


def render_file(file, args):
    body = open(file).read()
    if str(file).endswith('.md'):
        out = Template(body,
                       preprocessor=md_preprocessor,
                       strict_undefined=True).render(**args)
        return markdown(out, extensions=[
            CodeHiliteExtension(
                guess_lang=False,
                linenums=False,
                noclasses=True,
            ),
            FencedCodeExtension(),
        ])
    else:
        return Template(body, strict_undefined=True).render(**args)
