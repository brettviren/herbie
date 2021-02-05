import time
import sexpdata
from anytree import Node
from anytree.resolver import Resolver, ChildResolverError
from importlib import import_module


def select_window(wm, ui, tags = None, ignore_focus=True,
                  pattern = '[{tag}]\t{instance}\t{title}\x00icon\x1f{instance}'):
    '''Use UI to select a window.

    Candidates offered depend on tags and ignore_focus.

    tags of None means current focused, "all" means all tags, "other"
    means all but current or tags may be a list of tag names.

    The pattern is used to form the line used in the UI.choose().

    '''
    ui.retform = 'i'            # index

    if tags is None:
        tags = [wm.focused_tag]
    elif isinstance(tags, str):
        if tags == "all":
            tags = wm.current_tags()
        if tags == "other":
            tags = wm.current_tags()
            tags.remove(wm.focused_tag)
    # else it is assumed to be a list

    wid_focus = None
    if ignore_focus:
        wid_focus = wm("attr clients.focus.winid")

    winfos = dict()
    for tag in tags:
        for one in wm.winfos(tag):
            winfos[one['winid']] = one

    bytime = list(sorted(winfos.values(),
                    key=lambda o: o['my_focus_time']))

    bytime.reverse()

    now = time.time()
    lines = list()
    lines_invis = list()
    focus_line = None
    focus_choice = None
    choice = list()
    choice_invis = list()
    for winfo in bytime:
        dt = now - winfo['my_focus_time']
        line = pattern.format(dt=int(dt), **winfo)
        if winfo['winid'] == wid_focus:
            focus_line = line
            focus_choice = winfo
            continue
        if winfo['visible']:
            lines.append(line)
            choice.append(winfo)
        else:
            lines_invis.append(line)
            choice_invis.append(winfo)

    lines += lines_invis
    choice += choice_invis
    if focus_line:
        lines.append(focus_line)
        choice.append(focus_choice)
    ui.lines = len(lines)
    got = ui.choose(lines, 'Select window: ')
    if got is None:
        return
    try:
        got = int(got)
    except ValueError:
        return

    return choice[int(got)]['winid']
    


def available(thing="task"):
    '''
    Return list of things available from a thing.
    '''
    mod = import_module(f'herbie.{thing}s')
    lines = list()
    for one in dir(mod):
        if one.startswith(thing + "_"):
            lines.append(one.split('_',1)[1])
    return lines

def get_task(task):
    '''
    Return named task tree.
    '''
    import herbie.tasks
    meth = getattr(herbie.tasks, 'task_'+task)
    return meth()

def stringify(something, ending=None):
    if not isinstance(something, str):
        # fixme: assume sequence, but better test for this type directly
        something = '\n'.join(something)
    if ending is not None:
        something += ending
    return something

def tree_from_sexp(sexp, parent=None):
    '''
    Interpret sexp as from "hc dump" and turn into node tree.
    '''
    index = 0
    if parent:
        index = len(parent.children)
    node = binode(parent, index)
    what = sexp.pop(0).value()
    for term in sexp:
        if isinstance(term, list):
            tree_from_sexp(term, node)
            continue
        val = term.value()
        if val.startswith("vertical:") or val.startswith("horizontal:"):
            parts = val.split(":")
            node.orient = parts.pop(0)
            node.ratio = float(parts.pop(0))
            if parts:
                node.selection=int(parts.pop(0))
            continue

        if val.startswith("grid:"):
            parts = val.split(":")
            node.orient = parts.pop(0)
            # fixme:
            node.grid = int(parts.pop(0))            
            continue

        if val.startswith("max:"):
            continue

        if val.startswith("0x"):
            wids = getattr(node, "wids", list())
            wids.append(val)
            node.wids = wids
            continue

        raise ValueError(f'Unknown: {term}')
    return node

def make_tree(dump):
    '''
    Parse output of "hc dump" into a tree
    '''
    sexp = sexpdata.loads(dump)
    return tree_from_sexp(sexp)

def binode(parent=None, name="",**kwds):
    '''
    Produce a node assuring a binary tree is kept
    '''
    if parent is None:
        return Node(name or "top", **kwds)
    n = len(parent.children)
    if n > 1:
        raise ValueError("binary tree")
    if not name:
        name=n
    return Node(name, parent=parent, **kwds)



def render_split(tree):
    '''
    Render tree as argument to 'hc load'
    '''
    split = getattr(tree, "split", None)
    if not split:
        return
    ratio = getattr(tree, "ratio", 0.5)

    csplits = list()
    for child in tree.children:
        csplit = render_split(child)
        if csplit:
            csplits.append(csplit)
    children = ''
    if csplits:
        children = ' '
        children += ' '.join(csplits)
    return f'(split {split}:{ratio}:0{children})'



def closescreen(wm, tag, goto=None):
    '''
    Close all windows in tag and then merge the tag away.

    If goto given, make it the current tag.
    '''
    ti = wm.taginfo(tag)
    mergeto = None
    for other in wm.taginfos:
        if other.name == tag:
            continue
        mergeto = other.name
        break

    text = wm(f'dump {tag}')
    #print ('dump:',text)
    have = make_tree(text)
    for node in [have] + list(have.descendants):
        wids = getattr(node, "wids", ())
        for wid in wids:
            wm.add(f'close {wid}')
    if not goto:
        goto = mergeto
    wm.add("focus_monitor 0")
    wm.add(f'use {goto}')
    if mergeto:
        wm.add(f'merge_tag {tag} {mergeto}')
    #print(wm._chain)
    wm.run()

def toscreen(wm, tag, tree):
    '''
    Put tree to tag, idempotently
    '''
    if tag is None:
        tag = task

    #print("Tree:",tree)
    
    try:
        wm.taginfo(tag)
    except KeyError:
        wm(f'add {tag}')

    layout = render_split(tree)
    if layout:
        #print("Layout:",layout)
        wm(f'load {tag} "{layout}"')

    text = wm(f'dump {tag}')
    #print ('dump:',text)
    have = make_tree(text)

    # walk tree and have, building as needed
    r = Resolver()
    for node in [tree] + list(tree.descendants):
        if not hasattr(node, 'command'):
            continue
        pathlist = [str(n.name) for n in node.path]
        path = '/'.join(pathlist)
        path = '/' + path
        try:
            got = r.get(have, path)
            got = getattr(got, "wids", None)
        except ChildResolverError:
            got = None
        if got:
            continue
        match = ' '.join(['%s="%s"'%(k,v) for k,v in node.match.items()])
        index = ''.join(pathlist[1:])
        wm.add(f'rule once {match} tag={tag} index={index} maxage=10')
        wm.add(f'spawn {node.command}')
    
    wm.add("focus_monitor 0")
    wm.add(f'use {tag}')
    wm.run()


