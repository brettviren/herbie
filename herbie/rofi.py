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
        #sys.stderr.write(load + '\n')
        self._wm(load),
        return BAIL


class LayoutSaveItem(LayoutItem):

    def __init__(self, text=None, **kwargs):
        super().__init__(text, **kwargs)
        if text is not None:
            self._lay = Layout(self._lay.name, self._cursexp)

    async def on_select(self, meta):
        add_store(self._wm, self._lay, self.tag),
        return BAIL


class LayoutDropItem(LayoutItem):

    def __init__(self, text=None, **kwargs):
        super().__init__(text, **kwargs)

    async def on_select(self, meta):
        del_store(self._wm, self._lay, self.tag),
        return BAIL
        

def layout_text(lay, match_sexp):
    if lay.sexp == match_sexp:
        return f'<span color="green">{lay.name}</span>'
    return f'<span color="red">{lay.name}</span>'
    

def layout_menu_one(name, kwargs, submenu=False):
    caps = name.capitalize()
    Item = globals()[f'Layout{caps}Item']

    items = []
    if submenu:
        items.append(menu.BackItem())
    for k in kwargs:
        items.append(Item(**k))
    m = menu.Menu(prompt=f"{caps} layout", items=items)
    if submenu:
        m = menu.NestedMenu(caps, m)
    return m


def layout_menu(wm, which=None, tag = None):

    tag = tag or wm.focused_tag
    cursexp = wm(f'dump {tag}').strip()
    oldlays = read_store(wm, tag)
    icons = make_icons(oldlays, tag)

    kwargs = list()
    for lay,icon in zip(oldlays,icons):
        kwargs.append(dict(
            text=layout_text(lay, cursexp), icon=icon,
            wm=wm, tag=tag, lay=lay, cursexp=cursexp))

    if which is None or which == "all":
        which = "load save drop".split()

    if isinstance(which, str):
        return layout_menu_one(which, kwargs)

    submenus = [layout_menu_one(one, kwargs, True) for one in which]

    return menu.Menu(prompt="Layout operation", items = submenus)

