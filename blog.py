# Copyright (c) 2009-2020, Diego Ongaro.
# Licensed under the BSD 2-Clause License.

from configparser import ConfigParser
from datetime import datetime, timezone
import os
from pathlib import Path
import PyRSS2Gen
import re

from template import render_file


def augment_config(config):
    for slug, values in config['blog'].items():
        values['slug'] = slug
        if 'tags' in values:
            values['tags'] = values['tags'].split()
        else:
            values['tags'] = []


def render_article(config, slug, args):
    dir = Path(config['env']['var'], 'blog', slug)
    try:
        blurb = render_file(dir.joinpath('blurb.html'), args)
    except IOError:
        blurb = render_file(dir.joinpath('blurb.md'), args)
    m = re.match('^(.*?)<hr( /)?>(.*)$', blurb, flags=re.DOTALL)
    if m is None:
        return {
            'blurb': blurb,
        }
    else:
        return {
            'blurb': m.group(1) + m.group(3),
            'summary': m.group(1),
        }


def article(config, slug):
    args = config['blog'][slug].copy()
    args.update(config['controller'])
    args['blurb'] = render_article(config, slug, args)['blurb']
    args['PAGE_TITLE'] = args['title']
    args['CONTENT'] = render_file(
        Path(config['env']['var'], 'templates', 'blog', 'one.html'),
        args)
    return render_file(Path(config['env']['var'], 'templates', 'base.html'), args)


def rss(config):
    controller = config['controller'].copy()
    controller['URL_PREFIX'] = controller['FULL_URL_PREFIX']
    controller['VAR_URL_PREFIX'] = controller['FULL_VAR_URL_PREFIX']

    items = []
    for slug in config['blog']:
        args = config['blog'][slug].copy()
        args.update(controller)
        items.append(PyRSS2Gen.RSSItem(
            title=re.sub('<wbr( /)?>', '', args['title']),
            link=args['FULL_URL_PREFIX'] + f'/blog/{slug}/',
            description=render_article(config, slug, args)['blurb'],
            guid=PyRSS2Gen.Guid(args['URL_PREFIX'] + f'/blog/{slug}/'),
            pubDate=datetime.fromisoformat(args['date']).astimezone(timezone.utc)))

    rss = PyRSS2Gen.RSS2(
        title='ongardie.net',
        link=controller['FULL_URL_PREFIX'] + '/blog/',
        description="Diego Ongaro's Blog",
        lastBuildDate=datetime.now(),
        items=items)
    return rss.to_xml(encoding='utf-8')


def index(config, *, tag=None):
    articles = []
    for slug in config['blog']:
        article = config['blog'][slug].copy()
        if tag is not None and tag not in article['tags']:
            continue
        article_args = article.copy()
        article_args.update(config['controller'])
        article.update(render_article(config, slug, article_args))
        articles.append(article)

    args = config['controller'].copy()
    if tag is None:
        args['PAGE_TITLE'] = 'Blog Index'
    else:
        args['PAGE_TITLE'] = f'Blog: {tag} Tag'
    args['articles'] = articles
    args['CONTENT'] = render_file(
        Path(config['env']['var'], 'templates', 'blog', 'index.html'), args)
    return render_file(Path(config['env']['var'], 'templates', 'base.html'), args)
