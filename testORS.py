#/urs/local/bin/env python

import ORS

infile = open( 'test.ob')
lex = ORS.Lexer( infile, 39)

lex.get()
for key in ORS.Lex.__dict__:
    if ORS.Lex.__dict__[ key] == lex.sym : print 'sym = ', key
print 'ival =', lex.ival
print 'rval =', lex.rval
print 'strval = "', lex.strval, '"' 
print 'id =', lex.id
print '@', infile.tell()
