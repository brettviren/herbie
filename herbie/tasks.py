from herbie.util import binode

def dev():
    top = binode(None, split="vertical", ratio=0.75)
    u = binode(top, split="horizontal", ratio=0.5)
    ul = binode(u, command="emacs", match={'class':'Emacs'})
    ur = binode(u, command="firefox-esr -P default-esr",
              match=dict(title='Mozilla Firefox'))
    d = binode(top, command="kitty", match={'class':'kitty'})
    #print (RenderTree(top))
    #print(render_split(top))
    return top
