import sexpdata
from anytree import Node
from anytree.resolver import Resolver, ChildResolverError

from herbie.stluft import WM

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




def toscreen(tag, tree):
    '''
    Put tree to tag, idempotently
    '''
    wm = WM()
    if tag not in wm.tags:
        wm(f'add {tag}')

    layout = render_split(tree)
    print(layout)
    wm(f'load {tag} "{layout}"')

    text = wm(f'dump {tag}')
    print (text)
    have = make_tree(text)

    # walk tree and have, building as needed
    r = Resolver()
    for node in tree.descendants:
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
    wm.run()

