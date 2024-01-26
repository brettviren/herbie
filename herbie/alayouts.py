#!/usr/bin/env python
'''
herbie support for layouts

This module holds ways to process information such given by "hc dump".

herbie stores layout data on a per tag basis in files under
   ~/.config/herbie/layouts/<tag>/<name>
'''

import os
import sys
from herbie.util import make_tree
from herbie.svg import make_icon
from collections import namedtuple
from pathlib import Path

# in herbie we use this object representation for all info about a
# "layout"
Layout = namedtuple("Layout", "name sexp")


base_path = Path.home() / ".config/herbie/layouts"

def tag_path(tag):
    return base_path / tag


def assuredir(p):
    if not p.exists():
        os.makedirs(p)


def layout_path(tag, name):
    p = tag_path(tag)
    n = name + ".layout"
    return p / n
    

def purge(tag):
    p = tag_path(tag)
    if p.exists():
        os.removedirs(p.resolve())


def read_store(tag):
    '''
    Return list of Layouts stored on given or focused tag.
    '''
    p = tag_path(tag)
    if not p.exists():
        return []
    return [Layout(name=one.stem, sexp=one.read_text().strip())
            for one in p.glob("*.layout")]


def add_store(lay, tag):
    '''
    Add lay to store for tag
    '''
    lp = layout_path(tag, lay.name)
    assuredir(lp.parent)
    lp.write_text(lay.sexp + "\n")


def del_store(lay, tag):
    '''
    Assure layout is no longer in store.
    '''
    lp = layout_path(tag, lay.name)
    os.remove(lp)


def write_store(layouts, tag):
    '''
    Save layouts to tag.
    '''
    for oen in layouts:
        add_store(one, tag)


def make_icons(oldlays, tag):
    ret = list()
    for lay in oldlays:
        tree = make_tree(lay.sexp)
        iname = f'herbie{tag}{lay.name}'
        fname = make_icon(iname, tree)
        ret.append(iname)
    return ret

def layout_text(lay, **kwds):
    return lay.name
    # if lay.sexp == match_sexp:
    #     return f'<span color="green">{lay.name}</span>'
    # return f'<span color="red">{lay.name}</span>'

if __name__ == '__main__':
    print (read_store("ohai"))
