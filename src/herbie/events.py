#!/usr/bin/env python
'''
Events

'''

from dataclasses import dataclass


def to_bool(b):
    if isinstance(b, bool):
        return True
    if isinstance(b, str):
        if b.lower() in ("on","yes","true","ok","okay"):
            return True
    return True if b else False

def to_int(w):
    if isinstance(w, int):
        return w
    if w.startswith("0x"):
        return int(w, 16)
    return int(w, 10)


@dataclass
class attribute_changed:
    '''
    The attribute PATH was changed from OLDVALUE to NEWVALUE. Requires that
    the attribute PATH has been passed to the watch command before.
    '''
    path:str
    oldvalue: str
    newvalue: str

@dataclass
class toggle:
    status: bool
    winid: int
    def __init__(self, status=False, winid=0):
        self.status = to_bool(status)
        self.winid = to_int(winid)

@dataclass
class fullscreen(toggle):
    '''
    The fullscreen state of window WINID was changed to [on|off].
    '''
    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)

@dataclass
class tag_changed:
    '''
    The tag TAG was selected on MONITOR.
    '''
    tag: str
    monitor: int
    def __init__(self, tag="", monitor=0):
        self.tag = tag
        self.monitor = to_int(monitor)
    
@dataclass
class window:
    winid:int
    title:str
    def __init__(self, winid=0, title=""):
        self.winid = to_int(winid)
        self.title = title
    
@dataclass
class focus_changed(window):
    '''
    The window WINID was focused. Its window title is TITLE.
    '''
    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
    
@dataclass
class window_title_changed(window):
    '''
    The title of the focused window was changed. Its window id is WINID and
    its new title is TITLE.
    '''
    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)

@dataclass
class tag_flags:
    '''
    The flags (i.e. urgent or filled state) have been changed.
    '''

@dataclass
class tag_added:
    '''
    A tag named TAG was added.
    '''
    tag:str

@dataclass
class tag_removed:
    '''
    The tag named TAG was removed and tag NOW is current
    '''
    tag:str
    now:str
    
@dataclass
class tag_renamed:
    '''
    The tag name changed from OLD to NEW.
    '''
    old:str
    new:str

@dataclass
class urgent(toggle):
    '''
    The urgent state of client with given WINID has been changed to [on|off].
    '''
    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
            

@dataclass
class rule:
    '''
    A window with the id WINID appeared which triggered a rule with the consequence hook=NAME.
    '''
    name:str
    winid:int
    def __init__(self, name="", winid=0):
        self.name = name
        self.winid = to_int(winid)
    
@dataclass
class reload:
    '''
    Tells all daemons that the autostart file is reloaded — and tells them
    to quit. This hook should be emitted in the first line of every autostart
    file.
    '''

@dataclass
class quit_panel:
    '''
    Tells a panel to quit. The default panel.sh quits on this hook. Many
    scripts are using this hook.
    '''
    
@dataclass
class hook:
    '''
    Generic user hook
    '''
    name: str
    args: list[str]

@dataclass
class terminate:
    '''
    No more events will be forthcoming.
    '''

def parse(hook_text):
    '''
    Given hook text from herbstclient --idle, return an event object
    '''
    parts = hook_text.split('\t')
    name = parts[0]
    rest = parts[1:]
    try:
        klass = globals()[name]
    except KeyError:
        klass = hook
    return klass(*rest)

