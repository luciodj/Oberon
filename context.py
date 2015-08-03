#!/usr/bin/env python

class typeEnum:
    string_, integer_, char_ = range( 3)

t = typeEnum()

class Sym:
    sym = 0 
    val = 0

def getString( s):
    ' modifies the object s passed to return a string'
    s.sym = t.string_
    s.val = 'text'

def getInteger( s):
    s.sym = t.integer_
    s.val = 1234


s = Sym()
print 's.sym = %d    s.val = %s',( s.sym, s.val)

getString( s)
print 's.sym = %d    s.val = %s',( s.sym, s.val)

getInteger( s)
print 's.sym = %d    s.val = %s',( s.sym, s.val)


