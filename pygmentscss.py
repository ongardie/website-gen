#!/usr/bin/env python3

import pygments.formatters
import re
import sys


def strip_comments(line):
    return re.sub(r"\s*/\*.*\*/\s*", "", line)


def print_style(style):
    # This is roughly equivalent to:
    #
    #     pygmentize -S default -f html -a 'pre:has(> code)' | sed 's/\./.hl-/;
    #
    # but this produces more compact output.

    print(f"/* pygments {style} style for code highlighting */")

    formatter = pygments.formatters.HtmlFormatter(
        style=style, classprefix="hl-", nowrap=True
    )
    print("\n".join(formatter.get_background_style_defs("pre:has(> code)")))

    print("pre > code {")

    style_to_selectors = {}
    for line in formatter.get_token_style_defs():
        line = strip_comments(line)
        m = re.search("^(.*) { (.*) }$", line)
        if m is None:
            print(line)
        else:
            selector, style = m.groups()
            if style in style_to_selectors:
                style_to_selectors[style].append(selector)
            else:
                style_to_selectors[style] = [selector]
    for style, selectors in style_to_selectors.items():
        print(", ".join(selectors), "{", style, "}")

    print("}")


if __name__ == "__main__":
    if len(sys.argv) == 2:
        print_style(sys.argv[1])
    else:
        print_style("default")
