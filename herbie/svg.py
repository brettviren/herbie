import os

def header(pixelw, pixelh, userw=None, userh=None):
    'Return SVG header content'
    userw = userw or pixelw
    userh = userh or pixelh

    return f'''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg
   xmlns:dc="http://purl.org/dc/elements/1.1/"
   xmlns:cc="http://creativecommons.org/ns#"
   xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
   xmlns:svg="http://www.w3.org/2000/svg"
   xmlns="http://www.w3.org/2000/svg"
   width="{pixelw}"
   height="{pixelh}"
   id="svg11300"
   version="1.0"
   viewBox="0 0 {userw} {userh}">
    '''

def trailer():
    'Return SVG trailer content'
    return "</svg>"

def rectangle(w,h, x=0, y=0, fill="white", stroke="black", strokewidth=1, rx=0, ry=0):
    'Return SVG content for a rectangle'
    return f"<rect fill='{fill}' stroke='{stroke}' stroke-width='{strokewidth}px' width='{w}' height='{h}' y='{y}' x='{x}' ry='{ry}' rx='{rx}' />"

def line(x1, y1, x2, y2, stroke = "black", strokewidth=1):
    '''
    Return SVG content for a line.
    '''
    return f"<line stroke='{stroke}' stroke-width='{strokewidth}' x1='{x1}' y1='{y1}' x2='{x2}' y2='{y2}' />"

def nested(tree, x, y, w, h, strokewidth=1):
    '''Produce nested box drawing given a tree made from "hc dump"
    assuming an outer rectangle with corner at (x,y) and shape (w,h).
    '''

    ratio = getattr(tree, "ratio", None)
    if ratio is None:
        #print("svg_tree:", tree)
        return []

    if tree.orient == "horizontal":
        lx = x + w * ratio
        lines = [line(lx, y, lx, y+h, strokewidth=strokewidth)]
        childs = tree.children
        if not childs:
            return lines
        #print("horizontal:", tree, "with", len(childs))
        lines += nested(childs[0],  x, y, w*ratio, h, strokewidth)
        lines += nested(childs[1], lx, y, w*(1.0-ratio), h, strokewidth)
        return lines

    # vertical
    ly = y + h * ratio
    lines = [line(x, ly, x+w, ly, strokewidth=strokewidth)]
    childs = tree.children
    #print("vertical:", tree, "with", len(childs))
    if not childs:
        return lines
    lines += nested(childs[0], x, y, w, h*ratio, strokewidth) 
    lines += nested(childs[1], x, ly, w, h*(1-ratio), strokewidth)
    return lines
        

def make_icon(name, tree, width = 100, height = 100):
    '''
    Generate icon representing tree, return filename.

    File is named so that "name" can be used to name the icon to rofi.
    '''
    lines = [ header(width, height) ]
    lines += [ rectangle(width, height) ]
    lines += nested(tree, 0, 0, width, height, 10)
    lines += [ trailer() ]
    text = '\n'.join(lines)

    # fixme: use xdg standards
    base = os.environ['HOME']
    filename = os.path.join(base, '.icons', name + '.svg')

    open(filename, 'wb').write(text.encode())
    return filename
