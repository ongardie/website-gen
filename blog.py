# Copyright (c) 2009-2024, Diego Ongaro.
# Licensed under the BSD 2-Clause License.

from configparser import ConfigParser
from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
import PyRSS2Gen
import re

from template import render_file


def augment_config(config):
    for slug, values in config["blog"].items():
        values["slug"] = slug
        if "tags" in values:
            values["tags"] = values["tags"].split()
        else:
            values["tags"] = []


def render_article(config, slug, args):
    dir = Path(config["env"]["var"], "blog", slug)
    try:
        blurb = render_file(dir.joinpath("blurb.html"), args)
    except IOError:
        blurb = render_file(dir.joinpath("blurb.md"), args)
    m = re.match("^(.*?)<hr( /)?>(.*)$", blurb, flags=re.DOTALL)
    if m is None:
        return {
            "blurb": blurb,
        }
    else:
        return {
            "blurb": m.group(1) + m.group(3),
            "summary": m.group(1),
        }


def article(config, slug):
    args = config["blog"][slug].copy()
    args.update(config["controller"])
    args["FULL_URL"] = f"{args['FULL_URL_PREFIX']}/blog/{slug}/"
    args["blurb"] = render_article(config, slug, args)["blurb"]
    args["PAGE_TITLE"] = args["title"]
    if "plaintitle" in args:
        args["PLAIN_TITLE"] = args["plaintitle"]
    else:
        args["PLAIN_TITLE"] = args["title"]
    args["OPENGRAPH"] = [
        ("og:type", "article"),
        ("og:description", args["description"]),
        ("og:article:published_time", args["date"][:10]),
        ("og:article:author", args["FULL_URL_PREFIX"] + args["AUTHOR_PAGE"]),
    ]
    args["CONTENT"] = render_file(
        Path(config["env"]["var"], "templates", "blog", "one.html"), args
    )
    return render_file(Path(config["env"]["var"], "templates", "base.html"), args)


def rss(config):
    controller = config["controller"].copy()
    controller["URL_PREFIX"] = controller["FULL_URL_PREFIX"]
    controller["VAR_URL_PREFIX"] = controller["FULL_VAR_URL_PREFIX"]
    now = datetime.now(timezone.utc)

    items = []
    for slug in config["blog"]:
        article = config["blog"][slug].copy()
        article_args = article.copy()
        article_args.update(controller)
        article.update(render_article(config, slug, article_args))

        if "plaintitle" not in article:
            article["plaintitle"] = article["title"]

        date = datetime.fromisoformat(article["date"]).astimezone(timezone.utc)
        if "summary" in article and (
            now - date > timedelta(days=5 * 365) or len(items) > 10
        ):
            description = f"""{article['summary']}
                <p><a href="{controller['FULL_URL_PREFIX']}/blog/{slug}/">Continue reading full article</a></p>
            """
        else:
            description = article["blurb"]

        items.append(
            PyRSS2Gen.RSSItem(
                title=article["plaintitle"],
                link=f"{controller['FULL_URL_PREFIX']}/blog/{slug}/",
                description=description,
                guid=PyRSS2Gen.Guid(f"{controller['URL_PREFIX']}/blog/{slug}/"),
                pubDate=date,
            )
        )

        if len(items) > 50:
            break

    rss = PyRSS2Gen.RSS2(
        title="ongardie.net",
        link=controller["FULL_URL_PREFIX"] + "/blog/",
        description=f"{controller['AUTHOR']}'s Blog",
        lastBuildDate=now,
        items=items,
    )
    return rss.to_xml(encoding="utf-8")


def index(config, *, tag=None):
    articles = []
    for slug in config["blog"]:
        article = config["blog"][slug].copy()
        if tag is not None and tag not in article["tags"]:
            continue
        article_args = article.copy()
        article_args.update(config["controller"])
        article.update(render_article(config, slug, article_args))
        articles.append(article)

    args = config["controller"].copy()
    if tag is None:
        args["PAGE_TITLE"] = "Blog Index"
    else:
        args["PAGE_TITLE"] = f"Blog: {tag} Tag"
    args["PLAIN_TITLE"] = args["PAGE_TITLE"]
    args["FULL_URL"] = args["FULL_URL_PREFIX"] + "/blog/"
    args["OPENGRAPH"] = [
        ("og:description", f"{args['AUTHOR']}'s blog."),
    ]
    args["articles"] = articles
    args["CONTENT"] = render_file(
        Path(config["env"]["var"], "templates", "blog", "index.html"), args
    )
    return render_file(Path(config["env"]["var"], "templates", "base.html"), args)
