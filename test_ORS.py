#!/usr/bin/env python

from ORS import Lex, Lexer

def printLex( symTuple):
    sym, arg = symTuple
    for key in Lex.__dict__:
        if Lex.__dict__[ key] == sym : print 'sym = ', key,
    if sym in [Lex.char_, Lex.int_, Lex.real_, Lex.string_]:
        print 'arg =', arg

def test_string():
    test = '@*2345'
    r = Lexer( iter( '"'+test+'"')).get()
    assert r == ( Lex.string_, test)

def test_identifier():
    test = 'alphabet'
    lex = Lexer( iter( test))
    assert lex.get() == ( Lex.ident_, test)

def test_numbers():
    test = '12345 12.345 12.3E-4 12X 0ABCDH'
    lex = Lexer( iter( test))
    assert lex.get() == ( Lex.int_, 12345)
    assert lex.get() == ( Lex.real_, 12.345)
    assert lex.get() == ( Lex.real_, 12.3E-4)
    assert lex.get() == ( Lex.char_, 0x12)
    assert lex.get() == ( Lex.int_, 0xABCD)
    assert lex.get() == ( Lex.eof_, None)

def test_symbols():
    test = '+ - * / & | ~ ^ .. >= <= > < = # . , ; : := { } [ ]'
    lex = Lexer( iter( test))
    assert lex.get() == ( Lex.plus_, None)
    assert lex.get() == ( Lex.minus_, None)
    assert lex.get() == ( Lex.times_, None)
    assert lex.get() == ( Lex.rdiv_, None)
    assert lex.get() == ( Lex.and_, None)
    assert lex.get() == ( Lex.bar_, None)
    assert lex.get() == ( Lex.not_, None)
    assert lex.get() == ( Lex.arrow_, None)
    assert lex.get() == ( Lex.upto_, None)
    assert lex.get() == ( Lex.geq_, None)
    assert lex.get() == ( Lex.leq_, None)
    assert lex.get() == ( Lex.gtr_, None)
    assert lex.get() == ( Lex.lss_, None)
    assert lex.get() == ( Lex.eql_, None)
    assert lex.get() == ( Lex.neq_, None)
    assert lex.get() == ( Lex.period_, None)
    assert lex.get() == ( Lex.comma_, None)
    assert lex.get() == ( Lex.semicolon_, None)
    assert lex.get() == ( Lex.colon_, None)
    assert lex.get() == ( Lex.becomes_, None)
    assert lex.get() == ( Lex.lbrace_, None)
    assert lex.get() == ( Lex.rbrace_, None)
    assert lex.get() == ( Lex.lbrak_, None)
    assert lex.get() == ( Lex.rbrak_, None)
    assert lex.get() == ( Lex.eof_, None)

def test_keywords():
    test = '''IF DO OF OR TO IS BY IN END 
    ELSE THEN ELSIF FALSE REPEAT RETURN  PROCEDURE'''
    lex = Lexer( iter( test))
    assert lex.get() == ( Lex.if_, None)
    assert lex.get() == ( Lex.do_, None)
    assert lex.get() == ( Lex.of_, None)
    assert lex.get() == ( Lex.or_, None)
    assert lex.get() == ( Lex.to_, None)
    assert lex.get() == ( Lex.is_, None)
    assert lex.get() == ( Lex.by_, None)
    assert lex.get() == ( Lex.in_, None)
    assert lex.get() == ( Lex.end_, None)
    assert lex.get() == ( Lex.else_, None)
    assert lex.get() == ( Lex.then_, None)
    assert lex.get() == ( Lex.elsif_, None)
    assert lex.get() == ( Lex.false_, None)
    assert lex.get() == ( Lex.repeat_, None)
    assert lex.get() == ( Lex.return_, None)
    assert lex.get() == ( Lex.procedure_, None)
    assert lex.get() == ( Lex.eof_, None)

def test_negatives():
    test = ' ` _ 0i name* '
    lex = Lexer( iter( test))
    assert lex.get() == ( Lex.null_, None)
    assert lex.get() == ( Lex.null_, None)
    assert lex.get() == ( Lex.int_, 0)
    assert lex.get() == ( Lex.ident_, 'i')
    assert lex.get() == ( Lex.ident_, 'name')
    assert lex.get() == ( Lex.times_, None)
    assert lex.get() == ( Lex.eof_, None)

