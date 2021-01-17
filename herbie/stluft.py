import shlex
import subprocess
from collections import namedtuple

TagInfo = namedtuple("TagInfo","name index status")

class WM:
    'Make a call on herbstluftwm'

    def __init__(self, herbclient='herbstclient', delim = '.'):
        self.env = None         # allow override
        self._hc = herbclient
        self._chain = list()
        self._delim = delim

    def _parse_command(self, cmd):
        if isinstance(cmd, list):
            args = [str(x) for x in cmd]
            assert args
        else:
            args = shlex.split(cmd)
        return args
        
    def add(self, cmd):
        '''
        Add a command to me.
        '''
        if self._chain:
            self._chain.append(self._delim)
        self._chain += self._parse_command(cmd)

    def call(self, cmd):
        args = self._parse_command(cmd)
        print(args)
        proc = subprocess.run(
            [self._hc, '-n'] + args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=self.env,
            universal_newlines=True,
            # Kill hc when it hangs due to crashed server:
            timeout=2
        )
        return proc        

    def __call__(self, cmd):
        '''
        Immediately make a call on the WM
        '''
        proc = self.call(cmd)
        if proc.returncode:
            raise RuntimeError(f'{self._hc} {cmd} failed:\n{proc.stderr}')
        return proc.stdout

    def run(self):
        '''
        Run accumulated commands
        '''
        chain = ["chain", self._delim] + self._chain
        proc = self.call(chain)
        print(proc.stdout)
        print(proc.stderr)
        if proc.returncode:
            raise RuntimeError(f'{self._hc} {cmdstr} failed:\n{proc.stderr}')

    def taginfo(self, name_or_index=None):
        if type(name_or_index) not in (str, int):
            raise ValueError('taginfo requires a tag name or index')
        if isinstance(name_or_index, int):
            return self.taginfos[name_or_index]
        for ti in self.taginfos:
            if ti.name == name_or_index:
                return ti
        raise KeyError(f'no such tag: {name_or_index}')

    @property
    def taginfos(self):
        '''
        Return ordered array of tags
        '''
        text = self("tag_status")
        parts = text.strip().split('\t')

        tis = list()
        for index,part in enumerate(parts):
            status = part[0]
            name = part[1:]
            ti = TagInfo(name, index, status)
            tis.append(ti)
        return tis

