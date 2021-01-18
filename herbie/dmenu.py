#!/usr/bin/env python
import sys
import subprocess
import herbie.term
from herbie.util import stringify

def dmenu(lines, prompt=None):
    cmd = ["dmenu","-b","-i","-l","10"]
    if prompt:
        cmd += ["-p",prompt]
    # fixme: customization for fonts/colors

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

def echo(text, title=None):
    dmenu(stringify(text), title)
    
def choose(choices, prompt):
    return dmenu(stringify(choices), prompt)
