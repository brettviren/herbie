#!/usr/bin/env python3
'''
A terminal based menu
'''
from herbie.util import stringify
def echo(text, title=None):
    if title:
        print(stringify(title))
    print(stringify(text))

def choose(choices, prompt):
    echo(stringify(choices, '\n'))
    return input(prompt)

    
