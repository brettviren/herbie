#!/usr/bin/env python
'''
herbie support for layouts

This module holds ways to process information such given by "hc dump".

herbie can store possible layouts in herbstlufwm on a per tag basis
for latter re-application and simultaneously in an sqlite file so that
layouts survive herbstluftwm restarts.

'''

from herbie.util import make_tree
from herbie.svg import make_icon
from collections import namedtuple
import herbie.db as hdb

# in herbie we use this object representation for all info about a
# "layout"
Layout = namedtuple("Layout", "name sexp")

def unique(lays):
    '''
    Given a list of layouts, return another list with any with
    duplicate names removed.

    First one wins
    '''
    got = set()
    ret = list()
    for lay in lays:
        if lay.name in got:
            continue
        ret.append(lay)
        got.add(lay.name)
    return ret

# the attribute to name used to store layouts on a tag.  Actual name
# has "my_" prepended.
attr_name = 'layouts'

def purge(wm, tag=None):
    wm.del_my_attr(attr_name, tag)


NUL = '\0'
GS = '\x1d'                    # ascii group separator
RS = '\x1e'                    # ascii record separator
US = '\x1f'                    # ascii unit separator


def decode_saved(text):
    'Parse text form as might be saved to attr'
    if not text:
        return []
    groups = text.split(GS)
    return [Layout(*group.split(RS)) for group in text.split(GS)]

        
def encode_saved(layouts):
    'Serialize list of layouts to text form'
    return GS.join([RS.join(l) for l in layouts])


def sync_store(wm, tag=None):
    '''
    Assure db and wm stores are same for tag
    '''
    tag = tag or wm.focused_tag
    text = wm.get_my_attr(attr_name, tag)
    inwm = decode_saved(text)
    indb = hdb.get_layouts(tag)
    join = unique(inwm + indb)
    hdb.set_layouts(tag, join)
    return join


def read_store(wm, tag=None):
    '''
    Return list of Layouts stored on given or focused tag.
    '''
    return sync_store(wm, tag)


def add_store(wm, lay, tag=None):
    '''
    If lay is found by name in store, set its sexp, else append.
    '''
    lays = read_store(wm, tag)
    lays = list(filter(lambda l: l.name != lay.name, lays))
    lays.append(lay)
    write_store(wm, lays, tag)


def del_store(wm, lay, tag=None):
    '''
    If lay is found by name in store, remove it.
    '''
    tag = tag or wm.focused_tag
    lays = read_store(wm, tag)
    keep = list()
    drop = list()
    for have in lays:
        if have.name == lay.name:
            drop.append(lay.name)
        else:
            keep.append(have)
    hdb.del_layouts(tag, drop)
    write_store(wm, keep, tag)


def write_store(wm, layouts, tag=None):
    '''
    Save layouts to wm
    '''
    tag = tag or wm.focused_tag
    text = encode_saved(layouts)
    wm.set_my_attr(attr_name, text, tag)
    sync_store(wm, tag)

def make_icons(oldlays, tag):
    ret = list()
    for lay in oldlays:
        tree = make_tree(lay.sexp)
        iname = f'herbie{tag}{lay.name}'
        fname = make_icon(iname, tree)
        ret.append(iname)
    return ret


def rofi(wm, tag, oldlays, cursexp=None):
    '''Return text rendered for rofi representing stored and current layout.

    If cursexp is given and it matches and existing saved tree
    then the render will emphasize this.
    '''
    lines = []
    index = dict()
    for lay in oldlays:

        #print ("cur:",cursexp)
        #print ("lay:",lay.sexp)
        # if cursexp and cursexp == lay.sexp:
        #     lname = f'<span color="green">{lay.name}</span>'
        # else:
        #     lname = f'<span color="red">{lay.name}</span>'
        lname = lay.name

        tree = make_tree(lay.sexp)
        iname = f'herbie{tag}{lay.name}'
        fname = make_icon(iname, tree)
        line = f'{lname}{NUL}icon{US}{iname}{NUL}name{US}{lay.name}'
        lines.append(line)
        index[lname] = lay
    return lines, index
