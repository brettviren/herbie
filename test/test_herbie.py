from anytree import Node, RenderTree

def _test_commands():
    '''
    Build up a screen with raw commands
    '''
    wm = WM()
    tag="dev"
    wm.add(f"focus_monitor 0")
    wm.add(f"add {tag}")
    wm.add(f"use {tag}")
    wm.add(f"load {tag} '(split vertical:0.75:0 (split horizontal:0.5:0))'")
    wm.add(f"rule class=Emacs               tag={tag} index=00 maxage=10")
    wm.add(f"rule title='Mozilla Firefox'   tag={tag} index=01 maxage=10")
    wm.add(f"rule class=kitty               tag={tag} index=1 maxage=10")
    wm.add("list_rules")
    wm.run()
    subprocess.Popen(["emacs"])
    subprocess.Popen(["kitty"])
    subprocess.Popen(["firefox-esr","-P","default-esr"])


def test_node():
    top = binode(None, split="vertical", ratio=0.75)
    u = binode(top, split="horizontal", ratio=0.5)
    ul = binode(u, command="emacs", match={'class':'Emacs'})
    ur = binode(u, command="firefox-esr -P default-esr",
              match=dict(title='Mozilla Firefox'))
    d = binode(top, command="kitty", match={'class':'kitty'})
    print (RenderTree(top))
    print(render_split(top))
    return top

def test_toscreen():
    top = test_node()
    toscreen("test", top)

def test_sexp():
    # eg from hc dump
    text = '(split vertical:0.75:0 (split horizontal:0.5:0 (clients vertical:1 0x1e00142 0x3200142) (clients vertical:1 0x1200003 0x1200024)) (clients vertical:1 0x1c0000e 0x300000e))'
    top = make_tree(text)
    print (RenderTree(top))
    print(render_split(top))


