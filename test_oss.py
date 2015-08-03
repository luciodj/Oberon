#!/usr/bin/env python

from oss import Lex, Lexer

def printLex( symTuple):
    sym, arg = symTuple
    for key in Lex.__dict__:
        if Lex.__dict__[ key] == sym : print 'sym = ', key,
    if sym in [Lex.char_, Lex.int_, Lex.real_, Lex.string_]:
        print 'arg =', arg

def test_string():
    test = '@*2345'
    lex = Lexer( iter( '"'+test+'"' + ' $4041$'))
    assert (lex.get(), lex.value) == ( Lex.string_, test)
    assert (lex.get(), lex.value) == ( Lex.string_, '@A')

def test_identifier():
    test = 'alphabet'
    lex = Lexer( iter( test))
    r = lex.get(), lex.value
    assert r == ( Lex.ident, test)

def test_numbers():
    test = '12345 12.345 12.3E-4 12X 0ABCDH'
    lex = Lexer( iter( test))
    assert (lex.get(), lex.value) == ( Lex.int_, 12345)
    assert (lex.get(), lex.value) == ( Lex.real, 12.345)
    assert (lex.get(), lex.value) == ( Lex.real, 12.3E-4)
    assert (lex.get(), lex.value) == ( Lex.char_, 0x12)
    assert (lex.get(), lex.value) == ( Lex.int_, 0xABCD)
    assert (lex.get(), lex.value) == ( Lex.eof_, None)

def test_symbols():
    test = '+ - * / & | ~ ^ .. >= <= > < = # . , ; : := { } [ ]'
    lex = Lexer( iter( test))
    assert lex.get() == Lex.plus
    assert lex.get() == Lex.minus
    assert lex.get() == Lex.times
    assert lex.get() == Lex.rdiv
    assert lex.get() == Lex.and_
    assert lex.get() == Lex.bar
    assert lex.get() == Lex.not_
    assert lex.get() == Lex.arrow
    assert lex.get() == Lex.upto
    assert lex.get() == Lex.geq
    assert lex.get() == Lex.leq
    assert lex.get() == Lex.gtr
    assert lex.get() == Lex.lss
    assert lex.get() == Lex.eql
    assert lex.get() == Lex.neq
    assert lex.get() == Lex.period
    assert lex.get() == Lex.comma
    assert lex.get() == Lex.semicolon
    assert lex.get() == Lex.colon
    assert lex.get() == Lex.becomes
    assert lex.get() == Lex.lbrace
    assert lex.get() == Lex.rbrace
    assert lex.get() == Lex.lbrak
    assert lex.get() == Lex.rbrak
    assert lex.get() == Lex.eof_

def test_keywords():
    test = '''IF DO OF OR TO IS BY IN END 
    ELSE THEN ELSIF FALSE REPEAT RETURN  PROCEDURE'''
    lex = Lexer( iter( test))
    assert lex.get() == Lex.if_
    assert lex.get() == Lex.do
    assert lex.get() == Lex.of
    assert lex.get() == Lex.or_
    assert lex.get() == Lex.to
    assert lex.get() == Lex.is_
    assert lex.get() == Lex.by
    assert lex.get() == Lex.in_
    assert lex.get() == Lex.end
    assert lex.get() == Lex.else_
    assert lex.get() == Lex.then
    assert lex.get() == Lex.elsif
    assert lex.get() == Lex.false_
    assert lex.get() == Lex.repeat
    assert lex.get() == Lex.return_
    assert lex.get() == Lex.procedure
    assert lex.get() == Lex.eof_

def test_negatives():
    test = ' ` _ 0i name* '
    lex = Lexer( iter( test))
    assert lex.get() == Lex.null
    assert lex.get() == Lex.null
    assert ( lex.get(), lex.value) == ( Lex.int_, 0)
    assert ( lex.get(), lex.value) == ( Lex.ident, 'i')
    assert ( lex.get(), lex.value) == ( Lex.ident, 'name')
    assert lex.get() == Lex.times
    assert lex.get() == Lex.eof_

if __name__ == '__main__':
    test_negatives()
    test_keywords()
    test_symbols()
    test_numbers()
    test_identifier()
    test_string()
