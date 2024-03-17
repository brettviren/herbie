#!/usr/bin/env python
'''Herbie menu

An async interface to a dmenu type of list item selection uesr interface.

'''

import asyncio
from asyncio.subprocess import PIPE
from dataclasses import dataclass
from typing import Any

import logging
log = logging.getLogger("herbie")

@dataclass
class Item:
    '''
    A menu item is presented to user for potential selection.
    '''
    text : str
    '''The content of the item presented to the user'''
    value : Any = None
    '''Opaque object for use by the caller'''
    icon : str = None
    '''Optional name of an icon'''

    def __str__(self):
        return self.text

    
@dataclass
class Menu:
    items: list[Item]
    '''List of menu items'''
    prompt : str = None
    '''Optional prompt'''
    message : str = None
    '''Optional informational message to the user'''
    
    
    def index(self, text: str) -> int:
        '''
        Return index of item with text or None
        '''
        for ind, item in enumerate(self.items):
            if text == item.text:
                return ind
        return None

    def __str__(self):
        return '\n'.join(map(str, self.items))

NUL = '\x00'
GS = '\x1d'                    # ascii group separator
RS = '\x1e'                    # ascii record separator
US = '\x1f'                    # ascii unit separator



@dataclass
class Rofi:
    '''
    A menu implemented with rofi.
    '''

    literal: bool = False
    monitor: str = None
    location: str = None
    multi_select: bool = False
    columns: int = None

    def monitor_options(self):
        option = {
            "focused": -1, "focused_window": -2, "atmouse": -3,
            "withfocus": -4, "withmouse": -5}
        if self.monitor is None:
            return []

        try:
            num = option[self.monitor]
        except KeyError:
            return []
        return ['-monitor', str(num)]

    def location_options(self):
        option = {
            "tl": 1, "tc": 2, "tr": 3,
            "ml": 8, "mc": 0, "mr": 4,
            "bl": 7, "bc": 6, "br": 5}
        if self.location is None:
            return []
        try:
            num = option[self.location]
        except KeyError:
            return []
        return ['-location', str(num)]

    def basic_command(self):
        # fixme: add support for monitor,location,width,font
        cmd = ["rofi", "-i", "-dmenu", "-format", "s", "-sep", RS]
        cmd += self.monitor_options()
        cmd += self.location_options()
        if not self.literal:
            cmd.append("-markup-rows")
        if self.multi_select:
            cmd.append("-multi-select")
        if self.columns:
            cmd += ["-columns", str(self.columns)]
        return cmd

    async def __call__(self, menu):
        '''
        Return list of selected text items.        
        '''

        lines = list()
        have_icons = False
        for item in menu.items:
            if item.icon:
                have_icons = True
                lines.append(f'{item.text}{NUL}icon{US}{item.icon}')
            else:
                lines.append(item.text)
        content = RS.join(lines)

        cmd = self.basic_command()
        if menu.prompt:
            cmd += ['-p',menu.prompt]
        if menu.message:
            cmd += ['-mesg', menu.message]
        if have_icons:
            cmd.append("-show-icons")

        proc = await asyncio.create_subprocess_exec(
            *cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)

        if not proc:
            cmdstr = ' '.join(cmd)
            raise RuntimeError(f'failed to run "{cmdstr}"')

        out,err = await proc.communicate(content.encode())
        if err:
            raise RuntimeError(err.strip())
        out = out.decode().strip()
        if not out:
            return list()
        return out.split("\n")


async def example():
    lname = f'<span color="red">foo🧼</span>'

    menu = Menu([
        Item(f'{lname} {icon}', icon=icon, value=icon)
        for icon in ('firefox128', 'herbieohaibar', 'fullscreen')],
                prompt="hmenu test", message="pick favorite")

    print(menu)

    render = Rofi(multi_select=True)

    for text in await render(menu):
        ind = menu.index(text)
        print(f'[{ind}] "{text}" ({menu.items[ind].value})')

    
if '__main__' == __name__:
    asyncio.run(example())

# print('test\ttest\ttest\00icon\1ffullscreen')
# for icon in ''.split():
#     # print(f'myentry\0icon\x1f{icon}')
#     print(f'{lname}\t{icon}{NUL}icon{US}{icon}')
