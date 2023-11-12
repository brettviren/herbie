#!/usr/bin/env python3
'''A companion to herbstluftwm.
'''

import asyncio
from collections import defaultdict
import configparser
from pathlib import Path
import os
import sys

from anytree.resolver import Resolver, ChildResolverError

from herbie.util import make_tree, render_split
from herbie.hmenu import Menu, Item, Rofi 
# fixme: fix name. these are not async, but are "new style"
import herbie.alayouts as layouts
from herbie.astluft import *

import logging
log = logging.getLogger("herbie")

def set_logging(log_level = "DEBUG", log_file = None):
    log.setLevel(log_level)
    fmt = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    if log_file is None:
        hand = logging.StreamHandler()
    else:
        hand = logging.FileHandler(log_file)
    hand.setLevel(log_level)
    hand.setFormatter(fmt)
    log.addHandler(hand)

class Herbie:

    def __init__(self, cfg):
        self.cfg = cfg
        self.wincfg = dict()
        for sec in self.cfg:
            if not sec.startswith("window "):
                continue
            _, name = sec.split(' ', 1)
            secd = dict()
            for k in cfg[sec]:
                secd[k] = cfg[sec][k]
            self.wincfg[name] = secd


    async def run(self):
        await init_my_focus_time()

        idle = await asyncio.create_subprocess_exec(
            'herbstclient', '--idle',
            stdout=asyncio.subprocess.PIPE)

        while True:

            line = await idle.stdout.readline()
            line = line.decode().strip()
            if not line:
                break
            parts = line.split("\t")
            hook = parts[0]

            meth = getattr(self, hook, None)
            if not meth:
                log.debug(f'no hook for {parts}')
                continue

            log.debug(f'hooking: [{len(parts)}] {parts}')
            await meth(*parts)
    
    async def tag_added(self, name, tag):
        time = now()
        await hc(*f'new_attr string tags.by-name.{tag}.my_focus_time {time}'.split())

    async def tag_canged(self, name, tag, num):
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
            wid = history[1][0]
            await hc("jumpto", wid)


    async def reload(self, name):
        '''
        Restart self.
        '''
        log.info("reloading")
        os.execv(__file__, sys.argv)
        log.info("reloaded")


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
            return
        task_name = got[0]

        ind = menu.index(task_name)
        if ind is None:
            return

        await hc(f'add {task_name}')

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
                match = ' '.join(['%s="%s"'%(k,v) for k,v in wc.items()])
                index = ''.join(pathlist[1:])
                print(f'index:{index} match:{match}')
                await hc(f'rule once {match} tag={task_name} index={index} maxage=10')
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
            Item("Minimize","set_attr clients.focus.minimized true","minimize"),
            Item("Close","close","close"),
            Item("Toggle fullscreen", "fullscreen toggle", "fullscreen"),
            Item("Toggle pseudotile", "pseudotile toggle"),
            Item("Toggle floating", "pseudotile floating"),
            ], "window operation")

        for tag,time in await tag_times():
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
        '''
        tag = await focused_tag()
        lays = layouts.read_store(tag)
        cursexp = await get_layout(tag)
        icons = layouts.make_icons(lays, tag)

        menu = Menu(list(), prompt="layout", message="Give new name to save current")
        for lay, icon in zip(lays, icons):
            text = layouts.layout_text(lay, cursexp)
            log.debug(f'LAYOUT {text=} {icon=} {lay=}')
            menu.items.append(Item(text, lay, icon))

        for text in await self.layout_load_render(menu):
            ind = menu.index(text)
            if ind is None:
                lay = layouts.Layout(text, cursexp)
                layouts.add_store(lay, tag)
                continue        # fixme: wise? subject to typos
            lay = lays[ind]
            cmd = ['load', lay.sexp]
            await hc(*cmd)

    layout_drop_render = Rofi(multi_select=True)
    async def layout_drop(self, name):
        '''
        Ask user for a layout to drop
        '''
        tag = await focused_tag()
        lays = layouts.read_store(tag)
        cursexp = await get_layout(tag)
        icons = layouts.make_icons(lays, tag)

        menu = Menu(list(), prompt="layout to drop")
        for lay, icon in zip(lays, icons):
            text = layouts.layout_text(lay, cursexp)
            log.debug(f'LAYOUT {text=} {icon=} {lay=}')
            menu.items.append(Item(text, lay, icon))

        for text in await self.layout_drop_render(menu):
            ind = menu.index(text)
            if ind is None:
                continue        # fixme: wise? subject to typos
            layouts.del_store(lays[ind], tag)
        
    window_select_render = Rofi(columns=3)
    async def _window_jump(self, want_tag=None):
        items = list()
        widtags = await window_ids(want_tag)

        tlen = 2+max([len(tag) for _,tag in widtags])
        winfos = [await window_info(wid) for wid,_ in widtags]
        clen = 2+max([len(winfo.get("class","")) for winfo in winfos])
        
        seen = set()
        for winfo, (wid, tag) in zip(winfos, widtags):
            if wid in seen:
                continue
            seen.add(wid)

            # class, instance, minimized, my_focus_time, tag, title, visible, winid
            if winfo.get("minimized", False):
                continue
            if want_tag and not winfo.get("visible", True):
                continue
            stag = f'[{tag}]'
            scls = '(' + winfo['class'] + ')'
            item = Item(f'{stag:{tlen}}\t{scls:{clen}}\t' + winfo['title'],
                        value=f'jumpto {wid}',
                        icon=winfo.get("instance",None))
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
        

def get_config(cfgfile = None):
    cfg = configparser.ConfigParser()

    home = Path(os.environ['HOME'])

    if not cfgfile:             # old spot
        cfgfile = home / ".herbierc"

    if cfgfile:
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
        

import click
@click.group()
@click.option("-h","--hc",default="herbstclient",
              help="Set the herbstclient executable name")
@click.option("-c","--config",
              type=click.Path(),
              help="Set configuration file")
@click.option("-l","--log-file", default=None, # fixme, use XDG
              help="Set log file, default is terminal")
@click.option("-L","--log-level", default="INFO",
              help="Set log level")
@click.pass_context
def cli(ctx, hc, log_file, log_level, config):
    import herbie.astluft
    herbie.astluft.herbstclient = hc
    set_logging(log_level.upper(), log_file)
    ctx.obj = Herbie(get_config(config))
    

@cli.command("hooks")
@click.pass_context
def hooks(ctx):
    '''
    Start herbie loop and respond react to herbstlufwm hooks
    '''
    asyncio.run(ctx.obj.run())

def main():
    cli(obj = None)


if '__main__' == __name__:
    main()
    
