#!/usr/bin/env python3
import sys
from .layouts import (
    add_store, del_store, read_store, make_icons, Layout)
import rofi_menu as menu

BAIL = menu.Operation(menu.OP_EXIT)

class LayoutItem(menu.Item):
    def __init__(self, text=None, **kwargs):
        if text is None:
            super().__init__()
            return

        self._wm = kwargs.pop("wm")
        self._tag = kwargs.pop("tag")
        self._lay = kwargs.pop("lay")
        self._cursexp = kwargs.pop("cursexp")
        super().__init__(text, **kwargs)

    @property
    def tag(self):
        return self._tag or self._wm.focused_tag


class LayoutLoadItem(LayoutItem):

    def __init__(self, text=None, **kwargs):
        super().__init__(text, **kwargs)

    async def on_select(self, meta):
        sexp = self._lay.sexp
        load = f'load {self.tag} "{sexp}"'
        self._wm(load),
        return BAIL


class LayoutDropItem(LayoutItem):

    def __init__(self, text=None, **kwargs):
        super().__init__(text, **kwargs)

    async def on_select(self, meta):
        del_store(self._wm, self._lay, self.tag),
        return BAIL
        

class LayoutSaveItem(LayoutItem):

    def __init__(self, text=None, **kwargs):
        super().__init__(text, **kwargs)
        if text is not None:
            self._lay = Layout(self._lay.name, self._cursexp)

    async def on_select(self, meta):
        add_store(self._wm, self._lay, self.tag),
        return BAIL


class LayoutSaveMenu(menu.Menu):

    def __init__(self, prompt=None, items=None, wm=None,
                 tag=None, sexp=None, **kwds):
        self._wm = wm
        self._tag = tag
        self._sexp = sexp
        super().__init__(prompt=prompt, items=items,
                         allow_user_input = True, **kwds)

    async def on_user_input(self, meta):
        if not all([meta.user_input, self._wm]):
            return menu.Operation(menu.OP_REFRESH_MENU)
        lay = Layout(meta.user_input, self._sexp)
        add_store(self._wm, lay, self._tag)
        return BAIL

def layout_text(lay, match_sexp):
    if lay.sexp == match_sexp:
        return f'<span color="green">{lay.name}</span>'
    return f'<span color="red">{lay.name}</span>'
    

def layout_menu_one(wm, name, tag, cursexp, kwargs, submenu=False):
    caps = name.capitalize()
    Item = globals()[f'Layout{caps}Item']

    items = []
    if submenu:
        items.append(menu.BackItem())
    for k in kwargs:
        items.append(Item(**k))

    if name == "save":
        m = LayoutSaveMenu(f"{caps} layout", items, wm,
                           tag, cursexp)
    else:
        m = menu.Menu(prompt=f"{caps} layout", items=items)
        

    if submenu:
        m = menu.NestedMenu(caps, m)
    return m


def layout_menu(wm, which=None, tag=None):

    tag = tag or wm.focused_tag
    cursexp = wm(f'dump {tag}').strip()
    oldlays = read_store(wm, tag)
    icons = make_icons(oldlays, tag)

    kwargs = list()
    for lay, icon in zip(oldlays,icons):
        if not lay.name:
            continue
        if not lay.sexp:
            continue
        text = layout_text(lay, cursexp)
        kwargs.append(dict(
            text=text, icon=icon,
            wm=wm, tag=tag, lay=lay, cursexp=cursexp))

    if which is None or which == "all":
        which = "load save drop".split()

    if isinstance(which, str):
        return layout_menu_one(wm, which, tag, cursexp, kwargs)

    submenus = [layout_menu_one(wm, one, tag, cursexp, kwargs, True) for one in which]

    return menu.Menu(prompt="Layout operation", items = submenus)


class HerbItem(menu.Item):
    def __init__(self, text=None, **kwargs):
        if text is None:
            self._command = None
            super().__init__()
            return
        self._wm = kwargs.pop("wm")
        self._command = kwargs.pop("command")
        super().__init__(text, **kwargs)

    async def on_select(self, meta):
        self._wm(self._command)
        return BAIL


def tags_arg(wm, tags=None):
    if tags is None or tags == "focus":
        return [wm.focused_tag]
    elif tags == "all":
        return wm.current_tags()
    elif tags == "other":
        tags = wm.current_tags()
        tags.remove(wm.focused_tag)
        return tags
    return tags

window_item_pattern = '[{tag}]\t{instance}\t{title}'

def window_cmd_menu(wm, tags, prompt, cmdpat):
    tags = tags_arg(wm, tags)

    items = list()
    for tag in tags:
        for winfo in wm.winfos(tag):
            text = window_item_pattern.format(**winfo)
            cmd = cmdpat.format(**winfo)
            item = HerbItem(text=text, icon=winfo['instance'], wm=wm, command=cmd)
            items.append(item)
    return menu.Menu(prompt=prompt, items=items)
    


def wbring_menu(wm, tags=None):
    tags = tags_arg(wm, tags)
    
    items = list()
    for tag in tags:
        for winfo in wm.winfos(tag):
            text = window_item_pattern.format(**winfo)
            cmd = 'bring {winid}'.format(**winfo)
            item = HerbItem(text=text, icon=winfo['instance'], wm=wm, command=cmd)
            items.append(item)
    return menu.Menu(prompt="Bring window", items = items)
    
