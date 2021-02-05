#!/usr/bin/env python3
'''
This is an opnionated GUI for "herbie -u gui [...]".
'''
import gi
gi.require_version('Notify', '0.7')
from gi.repository import Notify

import sys
import subprocess
import herbie.term
from herbie.util import stringify

locations = {
    "tl":1, "tc":2, "tr":3,
    "ml":8, "mc":0, "mr":4,
    "bl":7, "bc":6, "br":5}

def monitor(which):
    try:
        return str(int(which))
    except ValueError:
        pass
    option = {
        "focused":-1, "focused_window":-2, "atmouse":-3,
        "withfocus":-4, "withmouse":-5}
    try:
        return str(option[which])
    except KeyError:
        pass
    return str(which)


class UI:
    def __init__(self,
                 width=100,
                 location="mc",
                 monitor="focused",
                 lines=10,
                 retform="s",
                 font=None):
        self.width = width
        self.location = location
        self.monitor = monitor
        self.font = font
        self.lines = 10
        self.retform = retform

    @property
    def cmd(self):
        ret = ["rofi", "-i", "-dmenu", "-markup-rows", "-show-icons",
               "-columns", "3",
               "-monitor", monitor(self.monitor),
               "-location", str(locations[self.location]),
               "-width", str(self.width),
               "-format", self.retform,
               "-lines", str(self.lines)]
        if self.font:
            ret += ["-font", self.font]
        return ret

    def run(self, cmd, lines):
        
        # text = stringify(lines)
        if isinstance(lines, list):
            lines = '\n'.join(lines)
        print("gui.run:", type(lines), repr(lines))

        proc = subprocess.Popen(cmd,
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                universal_newlines=True,
                                )
        out,err = proc.communicate(lines)
        if err:
            herbie.term.echo(out)
        return out

    def echo(self, text, title=None):
        me = title or "herbie"
        text = stringify(text)
        Notify.init(me)
        msg = Notify.Notification.new(me, text, "dialog-information")
        msg.show()

    def choose(self, choices, prompt, title=None):
        cmd = self.cmd
        if title:
            cmd += ["-mesg", title]
        cmd += ["-p", prompt]
        return self.run(cmd, choices)


