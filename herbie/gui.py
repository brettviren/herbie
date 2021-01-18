#!/usr/bin/env python3
'''
This is an opnionated GUI for "herbie -u gui [...]".
'''
import gi
gi.require_version('Notify', '0.7')
from gi.repository import Notify

from herbie.util import stringify

import herbie.dmenu
choose = herbie.dmenu.choose

def echo(text, title=None):
    me = title or "herbie"
    text = stringify(text)
    Notify.init(me)
    msg = Notify.Notification.new(me, text, "dialog-information")
    msg.show()
    
