#!/usr/bin/env python3
'''
A terminal based menu
'''
import sys
from herbie.util import stringify
def echo(text, title=None):
    if title:
        sys.stderr.write(stringify(title, '\n'))
    sys.stderr.write(stringify(text, '\n'))

def choose(choices, prompt):
    echo(choices)
    return input(prompt)

    
