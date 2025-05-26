#!/usr/bin/env python
'''
herbie support for storing things in sqlite db.
'''

from pathlib import Path
from collections import namedtuple
import sqlite3

def connection(filename=None):
    '''
    Return a DB connection

    Filename can be a path to an sqlite db file or :memory: and if
    None will use default file location.
    '''
    if not filename:
        filename = Path.home() / ".local/share/herbie/layouts.db"
    elif filename != ":memory:":
        filename = Path(filename)
        if not filename.parent.exists():
            filename.parent.mkdir(parents=True)
        filename = filename.resolve()
    con = sqlite3.connect(filename)
    cur = con.cursor()
    cur.execute("""
CREATE TABLE IF NOT EXISTS layouts (
    tag TEXT NOT NULL,
    name TEXT NOT NULL,
    data TEXT,
    PRIMARY KEY (tag, name, data));""")
    cur.execute("""
CREATE UNIQUE INDEX IF NOT EXISTS tag_name_idx ON layouts (tag,name)
    """)
    return con


Layout = namedtuple("Layout", "name sexp")


def get_layouts(tag, conn=connection()):
    '''
    Return list of Layout for tag.
    '''
    q = "SELECT name,data FROM layouts where tag = ?"
    rows = conn.execute(q, (tag,)).fetchall()
    return [Layout(name=r[0], sexp=r[1]) for r in rows]


def add_layouts(tag, lays, conn=connection()):
    '''
    Add list of Layout to db associated with tag.
    
    This will update existing with same name.
    '''
    for lay in lays:
        q = f"""
INSERT INTO layouts (tag, name, data)
VALUES ('{tag}', '{lay.name}', '{lay.sexp}')
ON CONFLICT(tag, name)
DO UPDATE SET data=excluded.data"""
        conn.execute(q)
    conn.commit()

    
def set_layouts(tag, lays, conn=connection()):
    '''
    Make set of layouts for a tag as given, removing any exiting.
    '''
    conn.execute(f"DELETE FROM layouts WHERE tag = '{tag}'")
    add_layouts(tag, lays, conn);


def del_layouts(tag, names, conn=connection()):
    '''
    Remove set of layouts for a tag.
    '''
    for name in names:
        conn.execute(f"DELETE FROM layouts where tag = '{tag}' and name = '{name}'")
    conn.commit()
