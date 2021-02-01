#!/usr/bin/env python3
'''
A terminal based menu
'''
from herbie.util import stringify

class UI:

    def echo(self, text, title=None):
        if title:
            print(stringify(title))
        print(stringify(text))

    def choose(self, choices, prompt, title=None):
        if title:
            choices.insert(0, title)

        self.echo(stringify(choices, '\n'))
        return input(prompt + ": ")

    
