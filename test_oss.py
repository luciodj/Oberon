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
    assert r == ( Lex.ident_, test)

def test_numbers():
    test = '12345 12.345 12.3E-4 12X 0ABCDH'
    lex = Lexer( iter( test))
    assert (lex.get(), lex.value) == ( Lex.int_, 12345)
    assert (lex.get(), lex.value) == ( Lex.real_, 12.345)
    assert (lex.get(), lex.value) == ( Lex.real_, 12.3E-4)
    assert (lex.get(), lex.value) == ( Lex.char_, 0x12)
    assert (lex.get(), lex.value) == ( Lex.int_, 0xABCD)
    assert (lex.get(), lex.value) == ( Lex.eof_, None)

def test_symbols():
    test = '+ - * / & | ~ ^ .. >= <= > < = # . , ; : := { } [ ]'
    lex = Lexer( iter( test))
    assert lex.get() == Lex.plus_
    assert lex.get() == Lex.minus_
    assert lex.get() == Lex.times_
    assert lex.get() == Lex.rdiv_
    assert lex.get() == Lex.and_
    assert lex.get() == Lex.bar_
    assert lex.get() == Lex.not_
    assert lex.get() == Lex.arrow_
    assert lex.get() == Lex.upto_
    assert lex.get() == Lex.geq_
    assert lex.get() == Lex.leq_
    assert lex.get() == Lex.gtr_
    assert lex.get() == Lex.lss_
    assert lex.get() == Lex.eql_
    assert lex.get() == Lex.neq_
    assert lex.get() == Lex.period_
    assert lex.get() == Lex.comma_
    assert lex.get() == Lex.semicolon_
    assert lex.get() == Lex.colon_
    assert lex.get() == Lex.becomes_
    assert lex.get() == Lex.lbrace_
    assert lex.get() == Lex.rbrace_
    assert lex.get() == Lex.lbrak_
    assert lex.get() == Lex.rbrak_
    assert lex.get() == Lex.eof_

def test_keywords():
    test = '''IF DO OF OR TO IS BY IN END 
    ELSE THEN ELSIF FALSE REPEAT RETURN  PROCEDURE'''
    lex = Lexer( iter( test))
    assert lex.get() == Lex.if_
    assert lex.get() == Lex.do_
    assert lex.get() == Lex.of_
    assert lex.get() == Lex.or_
    assert lex.get() == Lex.to_
    assert lex.get() == Lex.is_
    assert lex.get() == Lex.by_
    assert lex.get() == Lex.in_
    assert lex.get() == Lex.end_
    assert lex.get() == Lex.else_
    assert lex.get() == Lex.then_
    assert lex.get() == Lex.elsif_
    assert lex.get() == Lex.false_
    assert lex.get() == Lex.repeat_
    assert lex.get() == Lex.return_
    assert lex.get() == Lex.procedure_
    assert lex.get() == Lex.eof_

def test_negatives():
    test = ' ` _ 0i name* '
    lex = Lexer( iter( test))
    assert lex.get() == Lex.null_
    assert lex.get() == Lex.null_
    assert ( lex.get(), lex.value) == ( Lex.int_, 0)
    assert ( lex.get(), lex.value) == ( Lex.ident_, 'i')
    assert ( lex.get(), lex.value) == ( Lex.ident_, 'name')
    assert lex.get() == Lex.times_
    assert lex.get() == Lex.eof_

