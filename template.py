# Copyright (c) 2009-2024, Diego Ongaro.
# Licensed under the BSD 2-Clause License.

from mako.template import Template
from markdown_it import MarkdownIt
import pygments
import re


# Prevent Mako from consuming trailing backslashes, as those are often used in
# code blocks.
def backslash_preprocessor(input):
    return re.sub(r"\\$", r"🔕TRAILINGBACKSLASH🔕", input, flags=re.M)


def backslash_postprocessor(input):
    return re.sub(r"🔕TRAILINGBACKSLASH🔕$", r"\\", input, flags=re.M)


# A line starting with a '##' is a comment in Mako and a header in Markdown.
# We want Markdown's meaning,
def md_preprocessor(input):
    return re.sub("^##", "#🤫LEADINGDOUBLECOMMENT🤫", input, flags=re.M)


def md_postprocessor(input):
    return re.sub("^#🤫LEADINGDOUBLECOMMENT🤫", "##", input, flags=re.M)


def highlighter(content, lang, attrs):
    if lang == "":
        return content
    lexer = pygments.lexers.get_lexer_by_name(lang)
    formatter = pygments.formatters.HtmlFormatter(classprefix="hl-", nowrap=True)
    return pygments.highlight(content, lexer, formatter)


def render_file(file, args):
    body = open(file).read()
    if str(file).endswith(".md"):
        out = backslash_postprocessor(
            md_postprocessor(
                Template(
                    body,
                    preprocessor=lambda input: md_preprocessor(
                        backslash_preprocessor(input)
                    ),
                    strict_undefined=True,
                ).render(**args)
            )
        )

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
        return backslash_postprocessor(
            Template(
                body, preprocessor=backslash_preprocessor, strict_undefined=True
            ).render(**args)
        )
