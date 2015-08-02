#!/usr/bin/env python

class typeEnum:
    scope, identifier = range(5, 15, 5)


class ObjDesc:
    def __init__( self, type, name):
        self.type = type
        self.name = name
        self.scope = None
        self.items = None
        
    def __repr__( self):
        if self.type == typeEnum.scope:
            if self.items:
                    return 'Scope: "%s"  Items:  %s ' %  (self.name, len(self.items))
            else:
                    return 'Scope: "%s"  Empty' % self.name

    def __iter__( self):
        return ObjDescIterator( self)


class ObjDescIterator:
    def __init__( self, obj):
        self.obj = obj

    def next( self):
        if self.obj == None:
            raise StopIteration
        else:
            t = self.obj
            self.obj = self.obj.scope
            return t


def newScope( name_):
    return ObjDesc( type=typeEnum.scope, name=name_)

def newIdentifier( name_):
    return ObjDesc( type=typeEnum.identifier, name=name_)


def buildTree( t):
    t.items = [ newIdentifier('a'), newIdentifier('b'), newIdentifier('c')]
    t.scope = newScope('locals')
    t.scope.items = [ newIdentifier('d'), newIdentifier('e')]

def buildList( t):
    t[0].items = [ newIdentifier('a'), newIdentifier('b'), newIdentifier('c')]
    t.append( newScope('locals'))
    t[1].items = [ newIdentifier('d'), newIdentifier('e')]

def scan( head):
    print 'Head:'
    for  t in head:
        print t

from itertools import ifilter

def findItem( head, name):
    if list( ifilter( lambda x: x.name==name, head)):
        print 'Found it'



tree = newScope('root')
buildTree( tree)
scan( tree)

listOfLists = [ newScope( 'root')]
buildList( listOfLists)
scan( listOfLists)
findItem( listOfLists, 'locals')
