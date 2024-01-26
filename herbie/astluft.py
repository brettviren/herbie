import asyncio
from datetime import datetime
from herbie.util import make_tree

import logging
log = logging.getLogger("herbie")

def now():
    return str(datetime.now().timestamp())

herbstclient = "herbstclient"

async def hc(*args):
    '''
    Call herbstclient.  If single arg, it will be split on spaces.
    '''
    if len(args) == 1 and isinstance(args[0],str):
        args = args[0].split(" ")

    log.debug(f'hc: {args}')    
    argstr = ' '.join(args)
    log.debug(f'hc: {argstr}')
    proc = await asyncio.create_subprocess_exec(
        herbstclient, *args,
        stdout=asyncio.subprocess.PIPE)
    got = await proc.stdout.read()
    got = got.decode()
    return got

async def load_layout(tag, sexp):
    '''
    Load a layout into tag.
    '''
    await hc('load', tag, sexp)

async def get_layout(tag):
    '''
    Return sexp representiation of layout
    '''
    got = await hc('dump', tag)
    return got.strip()

async def tags_arg(tags=None):
    '''
    Return tags.  Tags is None, "focus", "all", "other" else pass-through.
    '''
    if tags is None or tags == "focus":
        tags = [ await focused_tag() ]
    elif tags == "all":
        tags = await all_tags()
    elif tags == "other":
        tags = await all_tags()
        tag.remove( await focused_tag() )
    return tags


async def tag_status():
    text = await hc("tag_status")
    parts = text.strip().split('\t')
    tis = dict()
    for part in parts:
        status = part[0]
        name = part[1:]
        tis[name] = status
    return tis

async def window_info(wid):
    '''
    Return dict of attributes for window of given wid or "focus".
    '''
    lines = await hc(f'attr clients.{wid}')
    lines = lines.split('\n')
    lines = lines[lines.index(' V V V')+1:]

    ret = dict()
    for line in lines:
        line = line.strip()
        if not line:
            continue

        t,_,_ = line[:5].split(' ')
        k,v = line[6:].split(" = ")

        if t == "b":        # boolean
            v = v == "true"
        elif t == "c":      # color
            pass
        elif t == "i":      # integer
            v = int(v)
        elif t == "r":      # regex
            pass
        elif t == "s":      # string
            v = v[1:-1]     # remove quotes
            try:            # maybe a float as string
                v = float(v)
            except ValueError:
                pass
        elif t == "u":      # unsigned int
            v = int(v)
        else:
            v = None

        if v is None:
            continue
        ret[k] = v
    return ret
    

async def window_times(want_tag=None):
    '''
    Return list of tuples (wid,tag,time) 

    If want_tag is given, filter list to only include that tag
    '''
    cmd=["foreach","C",'clients.',
         'sprintf','T','%c.tag','C',
         'substitute','TAG','T',
         'sprintf','F','%c.my_focus_time','C',
         'substitute','FOCUS','F',
         'sprintf','W','%c.winid','C',
         'substitute','WINID','W',
         'echo','WINID','TAG','FOCUS']
    got = await hc(*cmd)
    ret = list()
    for one in got.split("\n"):
        one = one.strip()
        if not one:
            continue
        wid,tag,time = one.split()
        if want_tag and tag != want_tag:
            continue
        ret.append((wid, tag, float(time)))
    return sorted(ret, key=lambda tt: tt[2])


async def window_ids(want_tag=None):
    '''
    Return list of tuples (wid,tag) 

    If want_tag is given, filter list to only include that tag
    '''
    cmd=["foreach","C",'clients.',
         'sprintf','T','%c.tag','C',
         'substitute','TAG','T',
         'sprintf','W','%c.winid','C',
         'substitute','WINID','W',
         'echo','WINID','TAG']
    got = await hc(*cmd)
    ret = list()
    for one in got.split("\n"):
        one = one.strip()
        if not one:
            continue
        wid,tag = one.split()
        if want_tag and tag != want_tag:
            continue
        ret.append((wid, tag))
    return ret

async def window_ids_by_tag():
    ret = defaultdict(list)
    for wid,tag in await window_ids():
        ret[tag].append(wid)
    return wid

async def tag_times():
    '''
    Return list of tuples (tags,time)
    '''
    cmd=["foreach","T","tags.by-name.","sprintf","N",
         '%c.name',"T","substitute","NAME","N",
         "sprintf","F","%c.my_focus_time","T",
         "substitute","FOCUS","F",
         "echo","NAME","FOCUS"]
    got = await hc(*cmd)
    ret = list()
    for one in got.split("\n"):
        one = one.strip()
        if not one:
            continue
        tag,time = one.split()
        ret.append((tag, float(time)))
    return sorted(ret, key=lambda tt: tt[1])

async def focused_tag():
    got = await hc('get_attr','tags.focus.name')
    return got.strip()

async def focused_wid():
    got = await hc('get_attr', 'tags.focus.focused_client.winid')
    return got.strip()

async def all_tags():
    text = await hc("tag_status")
    parts = text.strip().split('\t')
    return tuple( [p[1:] for p in parts] )

async def init_my_focus_time():
    tagdots = await hc(*"complete 1 attr tags.by-name.".split())

    for tagdot in tagdots.split('\n'):
        parts = [t.strip() for t in tagdot.split('.') if t.strip()]
        if not parts:
            continue
        tag = parts[-1]
        time = now()
        attr = f'tags.by-name.{tag}.my_focus_time'
        cmd = ['or',',',
               'get_attr', attr, ',',
               'new_attr', 'string', attr, time]
        await hc(*cmd)

    clis = await hc(*'complete 1 attr clients.'.split())
    for cli in clis.split('\n'):
        parts = cli.strip().split('.')
        if len(parts) < 2:
            continue
        wid = parts[1].strip()
        if not wid.startswith('0x'):
            continue
        time = now()
        attr = f'clients.{wid}.my_focus_time'
        cmd = ['or',',',
               'get_attr', attr, ',',
               'new_attr', 'string', attr, time]
        await hc(*cmd)

async def clear_tag(tag, goto=None):
    '''
    Close all windows in a tag and remove tag.

    '''
    tags = await tag_status()
    mergeto = None
    for other in tags:
        if other == tag:
            continue
        mergeto = other
        break

    text = await hc(f'dump {tag}')
    have = make_tree(text)

    for node in [have] + list(have.descendants):
        wids = getattr(node, "wids", ())
        for wid in wids:
            await hc(f'close {wid}')
    if not goto:
        goto = mergeto
    await hc("focus_monitor 0")
    await hc(f'use {goto}')
    if mergeto:
        await hc(f'merge_tag {tag} {mergeto}')

    
