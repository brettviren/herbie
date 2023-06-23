#!/usr/bin/env python

import herbie.db as hdb

db = hdb.connection(":memory:")

fodder = hdb.Layout(
    name='test_layout',
    sexp='(split horizontal:0.44:1 (clients vertical:0) (clients max:1))')

def test_add_layouts():
    hdb.add_layouts("test_tag", [fodder], db)

def test_get_layouts():
    lays = hdb.get_layouts("test_tag", db)
    assert len(lays)==1
    lay = lays[0]
    assert lay.name=="test_layout"
    print (lay.sexp)
    
    
def test_del_layouts():
    hdb.del_layouts("test_tag", ["test_layout"])
