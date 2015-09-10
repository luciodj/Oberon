#!/usr/bin/env python
from  osp import parse

def test_parser( ):
    test1 = "MODULE Test;  CONST c = 1; BEGIN WriteInt( c);  END Test."
    assert parse( iter( test1))

def test_parser2( ):
    test2 = "MODULE Test;  VAR a : INTEGER; BEGIN a := 1 ; WriteInt( a);  END Test."
    assert parse( iter( test2))
    
def test_parser3( ):
    test3 = "MODULE Test;  VAR a : ARRAY 10 OF INTEGER; BEGIN IF a[1] = 0 THEN WriteInt( ORD(TRUE)); END END Test."
    assert parse( iter( test3))
