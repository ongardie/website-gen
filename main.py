#!/usr/bin/env python3

# Copyright (c) 2009-2020, Diego Ongaro.
# Licensed under the BSD 2-Clause License.

import argparse
import configparser
import csv
import os
from pathlib import Path
import re
import shutil

import blog
from template import render_file


def read_ini(filename):
    # By default, ConfigParser makes everything lowercase. This subclass opts
    # out of that behavior.
    class ConfigParser(configparser.ConfigParser):
        def optionxform(self, option):
            return option
    config = ConfigParser()
    config.read_file(open(filename))
    return {
        name: dict(section)
        for name, section in config.items()
        if name != 'DEFAULT' or len(section) > 0
    }


def write(path, data):
    print('Writing', path)
    os.makedirs(path.parent, exist_ok=True)
    open(path, 'w').write(data)


parser = argparse.ArgumentParser(
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    description='Generate a web site.')
parser.add_argument('--config', metavar='FILE', dest='config.ini',
                    default='../config.ini',
                    help='Path to config.ini file')
parser.add_argument('--var', metavar='DIR',
                    default='../var',
                    help='Path containing templates and content')
parser.add_argument('--output', metavar='DIR',
                    default='../build',
                    help='Path for generated files')


def main(env):
    config = {'env': env}
    config.update(read_ini(config['env']['config.ini']))
    config['controller']['VAR_URL_PREFIX'] = config['controller']['URL_PREFIX'] + '/var'
    config['controller']['FULL_VAR_URL_PREFIX'] = config['controller']['FULL_URL_PREFIX'] + '/var'
    config['static'] = read_ini(Path(config['env']['var'], 'staticpages.ini'))
    config['blog'] = read_ini(Path(config['env']['var'], 'blog', 'index.ini'))
    blog.augment_config(config)

    # Clear out build directory and copy var into it.
    print('Initializing', config['env']['output'])
    shutil.rmtree(config['env']['output'], ignore_errors=True)
    os.makedirs(config['env']['output'])
    shutil.copytree(config['env']['var'],
                    Path(config['env']['output'], 'var'),
                    ignore=shutil.ignore_patterns('.*'))

    # Write static pages
    for slug, values in config['static'].items():
        args = {
            'PAGE_TITLE': values['title'],
        }
        try:
            with open(
                Path(config['env']['var'], 'blurbs', slug, 'data.csv'),
                newline=''
            ) as csvfile:
                args['CSV'] = list(csv.DictReader(csvfile))
        except IOError:
            pass
        args.update(config['controller'])

        try:
            args['CONTENT'] = render_file(
                Path(config['env']['var'], 'blurbs', slug, 'blurb.html'), args)
        except IOError:
            args['CONTENT'] = render_file(
                Path(config['env']['var'], 'blurbs', slug, 'blurb.md'), args)

        write(Path(config['env']['output'],
                   *values['url'].split('/'),
                   'index.html'),
              render_file(Path(config['env']['var'], 'templates', 'base.html'),
                          args))

    # Write blog pages
    write(Path(config['env']['output'], 'blog', 'index.html'),
          blog.index(config))
    write(Path(config['env']['output'], 'blog', 'rss.xml'),
          blog.rss(config))
    all_tags = {
        tag
        for article in config['blog'].values()
        for tag in article['tags']
    }
    for tag in all_tags:
        write(Path(config['env']['output'], 'blog', '+' + tag, 'index.html'),
              blog.index(config, tag=tag))
    for slug, values in config['blog'].items():
        write(Path(config['env']['output'], 'blog', slug, 'index.html'),
              blog.article(config, slug))


if __name__ == '__main__':
    args = parser.parse_args()
    main(vars(args))
