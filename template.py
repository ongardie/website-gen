# Copyright (c) 2009-2024, Diego Ongaro.
# Licensed under the BSD 2-Clause License.

from mako.template import Template
from markdown_it import MarkdownIt
import pygments
import re


# A line starting with a '##' is a comment in Mako and a header in Markdown.
# We want Markdown's meaning,
def md_preprocessor(input):
    output = []
    for line in input.split("\n"):
        m = re.match(r"^[\t ]*(#{2,6}) (.*)$", line)
        if m is None:
            output.append(line)
        else:
            size = str(len(m.group(1)))
            output.append(f"<h{size}>{m.group(2)}</h{size}>")
    return "\n".join(output)


def highlighter(content, lang, attrs):
    if lang == "":
        return content
    lexer = pygments.lexers.get_lexer_by_name(lang)
    formatter = pygments.formatters.HtmlFormatter(classprefix="hl-", nowrap=True)
    return pygments.highlight(content, lexer, formatter)


def render_file(file, args):
    body = open(file).read()
    if str(file).endswith(".md"):
        out = Template(
            body, preprocessor=md_preprocessor, strict_undefined=True
        ).render(**args)

        return (
            MarkdownIt(
                "commonmark",
                {
                    "highlight": highlighter,
                },
            )
            .enable(["table", "strikethrough"])
            .render(out)
        )
    else:
        return Template(body, strict_undefined=True).render(**args)
