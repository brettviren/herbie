#!/usr/bin/env pytest
import pytest
from herbie.events import *

def test_parse():
    e = parse('focus_changed	0x140000b	herbstclient -i ~/d/herbie')
    assert(isinstance(e, focus_changed))
    assert(isinstance(e.winid, int))
    assert(e.winid == 0x140000b)

    e = parse('window_title_changed	0x140000b	~/d/herbie')
    assert(isinstance(e, window_title_changed))

    e = parse('tag_changed	ohai	0')
    assert(isinstance(e, tag_changed))
    assert(e.tag == 'ohai')
    assert(e.monitor == 0)

    e = parse('tag_added	ohai')
    e = parse('reload')
    e = parse('tag_flags')
    e = parse('tag_removed	foo	irc')
    e = parse('boogie	down	productions')
