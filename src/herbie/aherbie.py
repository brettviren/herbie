import os
import sys
import asyncio
import configparser
from pathlib import Path
from anytree.resolver import Resolver, ChildResolverError
from herbie.util import make_tree, render_split
from herbie.hmenu import Menu, Item, Rofi 
import herbie.alayouts as layouts

import logging
log = logging.getLogger("herbie")

from herbie.astluft import (
    hc, now, get_layout, tag_status, window_info,
    window_times, window_ids, tag_times, focused_tag,
    init_my_focus_time, clear_tag)

def get_config(cfgfile=None):
    cfg = configparser.ConfigParser()

    home = Path(os.environ['HOME'])

    if not cfgfile:             # old spot
        cfgfile = home / ".herbierc"

    if cfgfile.exists():
        log.info(f"loading {cfgfile}")
        cfg.read(cfgfile)
        return cfg

    # autoload using XDG patterns including looking into herbstluftwm
    base = os.environ.get("XDG_CONFIG_HOME", None)
    if not base:
        base = os.environ["HOME"] + "/.config"
    base = Path(base)
    for maybe in ["herbie", "herbstluftwm"]:
        cfgfile = base / maybe / "herbie.cfg"
        if cfgfile.exists():
            log.info(f"loading {cfgfile}")
            cfg.read(cfgfile)
    return cfg



class Herbie:

    def __init__(self, cfgfile):
        self.cfgfile = cfgfile
        self.cfg = get_config(cfgfile)
        self.wincfg = dict()
        for sec in self.cfg:
            if not sec.startswith("window "):
                continue
            _, name = sec.split(' ', 1)
            secd = dict()
            for k in self.cfg[sec]:
                secd[k] = self.cfg[sec][k]
            self.wincfg[name] = secd

    async def run(self):
        await init_my_focus_time()

        log.debug('starting herbstclient --idle')
        idle = await asyncio.create_subprocess_exec(
            'herbstclient', '--idle',
            stdout=asyncio.subprocess.PIPE)

        log.debug('looping on hooks')
        while True:

            line = await idle.stdout.readline()
            line = line.decode().strip()
            if not line:
                break
            parts = line.split("\t")
            hook = parts[0]

            meth = getattr(self, hook, None)
            if not meth:
                # log.debug(f'no hook for {hook}')
                continue

            log.debug(f'hooking: [{len(parts)}] {parts}')
            await meth(*parts)

    async def reinit_idle(self, name):
        autostart = Path(Path.home() / ".config/herbie/autostart")
        if autostart.exists():
            log.debug('running herbie autostart')
            proc = await asyncio.create_subprocess_exec(
                autostart,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE)
            stdout, stderr = await proc.communicate()
            if stdout:
                log.debug(stdout.decode())
            if stderr:
                log.warn(stderr.decode())


    async def tag_added(self, name, tag):
        time = now()
        await hc(*f'new_attr string tags.by-name.{tag}.my_focus_time {time}'
                 .split())

    async def tag_changed(self, name, tag, num):
        time = now()
        await hc(*f'set_attr tags.by-name.{tag}.my_focus_time {time}'.split())

    async def focus_changed(self, name, wid, title=None):
        if wid == '0x0':
            return
        time = now()
        await hc(*f'set_attr clients.{wid}.my_focus_time {time}'.split())

    async def last_window(self, name):
        '''
        Focus the previously focused window.
        '''
        tag = await focused_tag()
        history = await window_times(tag)
        log.debug(f'HISTORY {history}')
        if len(history) > 1:
            last = history[0]
            log.debug(f'JUMPTO {last}')
            wid = last[0]
            await hc("jumpto", wid)

    async def reload(self, name):
        '''
        Restart self.
        '''
        log.info("reloading")
        #os.execv(__file__, sys.argv)
        log.info(f'command: {sys.argv}')
        os.execv(sys.argv[0], sys.argv)
        log.info("reloaded") # this is never called

    task_menu_render = Rofi()

    async def task_start(self, name):
        '''
        Create a tag with a layout.
        '''
        tasks = self.cfg['tasks']
        items = list()
        for tname, task in tasks.items():
            items.append(Item(tname, value=task, icon=tname))
        log.debug(f"TASK START with {len(items)} known tasks")
        menu = Menu(items, prompt="Start a task")
        got = await self.task_menu_render(menu)
        if not got or not got[0]:
            log.debug('task menu returns nothing')
            return
        task_name = got[0]

        await hc(f'add {task_name}')

        ind = menu.index(task_name)
        if ind is None:
            log.debug(f'novel task "{task_name}"')
            # fixme: probably should save or something
            return

        task = items[ind].value
        tree = make_tree(task)
        sexp = render_split(tree)
        if sexp:
            cmd = ['load', task_name, sexp]
            await hc(*cmd)

        have = await hc(f'dump {task_name}')
        log.debug(f"start_task has layout: {have}")
        have = make_tree(have)

        r = Resolver()
        for node in [tree] + list(tree.descendants):
            if not hasattr(node, 'windows'):
                log.debug(f'no windows in {node}')
                continue
            pathlist = [str(n.name) for n in node.path]
            path = '/'.join(pathlist)
            path = '/' + path
            try:
                got = r.get(have, path)
                got = getattr(got, "wids", None)
            except ChildResolverError:
                got = None
            if got:
                log.debug(f'nothing for node {node}')
                continue
            for window in node.windows:
                wc = self.wincfg.get(window)
                if not wc:
                    log.debug(f'no wincfg for {window}')
                    continue
                command = wc.pop("command", None)
                if command is None:
                    continue
                match = ' '.join(['%s="%s"' % (k, v) for k, v in wc.items()])
                index = ''.join(pathlist[1:])
                print(f'index:{index} match:{match}')
                await hc(f'rule once {match} '
                         f'tag={task_name} index={index} maxage=10')
                await hc(f'spawn {command}')
        await hc("focus_monitor 0")
        await hc(f'use {task_name}')

        pass

    task_clear_render = Rofi(multi_select=True)

    async def task_clear(self, name):
        ts = await tag_status()

        current_tag = [t for t in ts if ts[t] == "#"][0]

        items = list()
        for tag in ts:
            items.append(Item(tag))
        menu = Menu(items, prompt="Select task tags to clear")
        for tag in await self.task_clear_render(menu):
            await clear_tag(tag, current_tag)

    window_menu_render = Rofi(location="tl", monitor="focused_window")

    async def window_menu(self, name):
        '''
        Open a window menu
        '''
        menu = Menu([
            Item("Minimize", "set_attr clients.focus.minimized true", "minimizen"),
            Item("Close", "close", "close"),
            Item("Toggle fullscreen", "fullscreen toggle", "fullscreen"),
            Item("Toggle pseudotile", "pseudotile toggle"),
            Item("Toggle floating", "pseudotile floating"),
            ], "window operation")

        for tag, time in await tag_times():
            item = Item(f'Move to tag {tag}', f'move {tag};use {tag}')
            menu.items.append(item)

        for text in await self.window_menu_render(menu):
            ind = menu.index(text)
            if ind is None:
                cmd = text
            else:
                cmd = menu.items[ind].value
            cmd = cmd.split(" ")
            await hc(*cmd)

    layout_load_render = Rofi()

    async def layout_load(self, name):
        '''
        Open a menu to select a layout to load.

        If name returned which is new, then save current to that name.
        '''
        tag = await focused_tag()
        lays = layouts.read_store(tag)
        cursexp = await get_layout(tag)
        icons = layouts.make_icons(lays, tag)

        menu = Menu(list(), prompt="layout to load",
                    message="New name saves current")
        for lay, icon in zip(lays, icons):
            menu.items.append(Item(lay.name, lay, icon))

        name = await self.layout_load_render(menu)
        if not name:
            return

        name = name[0]
        ind = menu.index(name)
        if ind is None and name not in lays:  # new
            lay = layouts.Layout(name, cursexp)
            layouts.add_store(lay, tag)
            return

        lay = lays[ind]
        cmd = ['load', lay.sexp]
        await hc(*cmd)

    async def layout_save(self, name):
        '''
        Save current layout.

        This may overwrite existing name.
        '''
        tag = await focused_tag()
        lays = layouts.read_store(tag)
        cursexp = await get_layout(tag)
        icons = layouts.make_icons(lays, tag)

        menu = Menu(list(), prompt="save layout to name")
        for lay, icon in zip(lays, icons):
            menu.items.append(Item(lay.name, lay, icon))

        name = await self.layout_load_render(menu)
        if not name:
            return

        name = name[0]
        lay = layouts.Layout(name, cursexp)
        layouts.add_store(lay, tag)

    layout_drop_render = Rofi(multi_select=True)

    async def layout_drop(self, name):
        '''
        Ask user for a layout to drop.

        If drop current then go to first remaining.
        '''
        tag = await focused_tag()
        lays = layouts.read_store(tag)
        cursexp = await get_layout(tag)
        icons = layouts.make_icons(lays, tag)

        menu = Menu(list(), prompt="layout to drop",
                    message="New name saves current")
        for lay, icon in zip(lays, icons):
            menu.items.append(Item(lay.name, lay, icon))

        drop_cur = False
        for name in await self.layout_drop_render(menu):
            ind = menu.index(name)
            if ind is None:     # new
                lay = layouts.Layout(name, cursexp)
                layouts.add_store(lay, tag)
                continue
            dead = lays[ind]
            lays[ind] = None
            if dead.sexp == cursexp:
                drop_cur = True
            log.debug(f'LAYOUT DROP {name=} {ind=} {dead=} {drop_cur=}')
            layouts.del_store(dead, tag)

        # drop the current layout, so pick first one and apply it.
        if drop_cur:
            for lay in lays:
                if lay is None:
                    continue
                cmd = ['load', lay.sexp]
                await hc(*cmd)
                return

    window_select_render = Rofi(columns=3)

    async def _window_jump(self, want_tag=None):
        items = list()
        widtags = await window_ids(want_tag)

        tlen = 2+max([len(tag) for _, tag in widtags])
        winfos = [await window_info(wid) for wid, _ in widtags]
        clen = 2+max([len(winfo.get("class", "")) for winfo in winfos])

        seen = set()
        for winfo, (wid, tag) in zip(winfos, widtags):
            if wid in seen:
                continue
            seen.add(wid)

            if winfo.get("minimized", False):
                continue
            if want_tag and not winfo.get("visible", True):
                continue
            stag = f'[{tag}]'
            scls = '(' + winfo['class'] + ')'
            item = Item(f'{stag:{tlen}}\t{scls:{clen}}\t' + winfo['title'],
                        value=f'jumpto {wid}',
                        icon=winfo.get("instance", None))
            items.append(item)
        menu = Menu(items, prompt="Jump to window")
        for text in await self.window_select_render(menu):
            ind = menu.index(text)
            if ind is None:
                continue
            await hc(menu.items[ind].value)

        pass

    async def window_jump_tag(self, name):
        '''
        Jump to a selected window in current tag.
        '''
        tag = await focused_tag()
        await self._window_jump(tag)

    async def window_jump_any(self, name):
        '''
        Jump to a selected window in any tag.
        '''
        await self._window_jump()
