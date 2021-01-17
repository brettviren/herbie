from herbie.util import binode

def task_irc():
    return binode(None, command="weechat.sh",
                  match={'name':'KittyWeechat'})

def task_dweb():
    return binode(None, command="firefox -P default-esr",
                  match=dict(title='Mozilla Firefox'))
def task_bweb():
    return binode(None, command="firefox -P brett",
                  match=dict(title='Mozilla Firefox'))

def task_rss():
    top = binode(None, split="horizontal", ratio=0.75)
    l = binode(top, command="firefox -P default-esr",
               match=dict(title='Mozilla Firefox'))
    r = binode(top, command="liferea",
               match={'class':'Liferea'})
    return top

def task_dev():
    top = binode(None, split="vertical", ratio=0.75)
    u = binode(top, split="horizontal", ratio=0.5)
    ul = binode(u, command="emacs", match={'class':'Emacs'})
    ur = binode(u, command="firefox -P default-esr",
              match=dict(title='Mozilla Firefox'))
    d = binode(top, command="kitty", match={'class':'kitty'})
    #print (RenderTree(top))
    #print(render_split(top))
    return top
