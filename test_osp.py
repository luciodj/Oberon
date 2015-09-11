#!/usr/bin/env python
from  osp import parse, gen

def test_parser( ):
    test1 = "MODULE Test;  CONST c = 1; BEGIN WriteInt( c);  END Test."
    assert parse( iter( test1))

def test_parser2( ):
    test2 = "MODULE Test;  VAR a : INTEGER; BEGIN a := 1 ; WriteInt( a);  END Test."
    assert parse( iter( test2))
    
def test_parser3( ):
    test3 = "MODULE Test;  VAR a : ARRAY 10 OF INTEGER; BEGIN IF a[1] = 0 THEN WriteInt( ORD(TRUE)); END END Test."
    assert parse( iter( test3))

def test_procedure():
    test = '''
    MODULE Test;
    VAR a: INTEGER;
    PROCEDURE Inc( VAR i:INTEGER);
    BEGIN
      i := i + 1;
    END Inc;
    BEGIN
        a := 1;
        Inc( a);
        WriteInt( a);
    END Test. '''
    parse( iter( test))
    bp = gen.pc
    # gen.Decode()
    gen.Execute()
    assert gen.code[ bp] == 2
