#!/usrbin/env python
""" 
    MODULE ORS; (* NW 19.9.93 / 1.4.2014  Scanner in Oberon-07 *)
    IMPORT SYSTEM, Texts, Oberon;

    Oberon Scanner does lexical analysis. Input is Oberon-Text, output is
    sequence of symbols, i.e identifiers, numbers, strings, and special symbols.
    Recognises all Oberon keywords and skips comments. The keywords are
    recorded in a table.
    get() delivers self.next symbol from input file
    mark(msg) records error and delivers error message stdout
    If get delivers ident, then the identifier (a string) is in variable id, if int or char
    in ival, if real in rval, and if string in str
"""
import sys
import string
 
IDLEN = 32
MAXEX = 38
STRINGLEN = 256

errcnt = 0
  
class Lex:    # lexical symbols
    null = 0; times = 1; rdiv = 2; div = 3; mod = 4;
    and_ = 5; plus = 6; minus = 7; or_ = 8; eql = 9;
    neq = 10; lss = 11; leq = 12; gtr = 13; geq = 14;
    in_ = 15; is_ = 16; arrow = 17; period = 18;
    char_ = 20; int_ = 21; real = 22; false_ = 23; true_ = 24;
    nil = 25; string_ = 26; not_ = 27; lparen = 28; lbrak = 29;
    lbrace = 30; ident = 31;
    if_ = 32; while_ = 34; repeat = 35; case = 36; for_ = 37;
    comma = 40; colon = 41; becomes = 42; upto = 43; rparen = 44;
    rbrak  = 45; rbrace = 46; then = 47; of = 48; do = 49;
    to = 50; by = 51; semicolon = 52; end = 53; bar = 54;
    else_ = 55; elsif = 56; until = 57; return_ = 58;
    array = 60; record = 61; pointer = 62; const = 63; type = 64;
    var = 65; procedure = 66; begin = 67; import_ = 68; module_ = 69; eof_ = 70

KeyTable = {  
    'IF': Lex.if_, 'DO' : Lex.do, 'OF': Lex.of,  'OR': Lex.or_, 'TO': Lex.to, 
    'IN': Lex.in_, 'IS': Lex.is_, 'BY': Lex.by, 
    'END': Lex.end, 'NIL': Lex.nil, 'VAR': Lex.var, 'DIV': Lex.div, 'MOD': Lex.mod, 
    'FOR': Lex.for_, 'ELSE': Lex.else_, 'THEN': Lex.then, 'TRUE': Lex.true_, 'TYPE': Lex.type, 
    'CASE': Lex.case, 'ELSIF': Lex.elsif, 'FALSE': Lex.false_, 'ARRAY': Lex.array, 
    'BEGIN': Lex.begin, 'CONST': Lex.const, 'UNTIL': Lex.until, 'WHILE': Lex.while_, 
    'RECORD': Lex.record, 'REPEAT': Lex.repeat, 'RETURN': Lex.return_, 'IMPORT': Lex.import_, 
    'MODULE': Lex.module_, 'POINTER': Lex.pointer, 'PROCEDURE': Lex.procedure
    }

def mark( msg):
    global errcnt, errpos, line, pos
    if line > errpos and errcnt < 25:
        print ; print '^'.rjust( 2 * (pos-1)) + msg
    errcnt += 1 
    errpos = line


class Lexer:
    def __init__( self, reader):
        global errpos, errcnt, line, pos
        self.reader = reader    
        errpos = 0
        errcnt = 0
        line = 1
        pos = 0
        self.ch = reader.next()
        # print self.ch, # dbg
        self.value = None

    def next( self):                    # get next character 
        global pos, line
        # self.ch = self.infile.read(1)
        print self.ch,  # dbg
        try: self.ch = self.reader.next()
        except StopIteration: self.ch = ''
        pos += 1
        if self.ch in '\r\n' : 
            line += 1; 
            pos = 0


    def getIdentifier( self):           # returns sym = keyword or ident
        ids = []
        while self.ch.isalnum() :
            ids.append( self.ch)
            self.next()
        ids = ''.join( ids)
        if ids in KeyTable : return KeyTable[ ids]
        else: self.value = ids[: IDLEN]; return Lex.ident

    def getString( self):
        self.next()
        s = []
        while (self.ch != '') and (self.ch != '"') : 
            if self.ch in string.printable :
                s.append( self.ch)
            self.next()
        s = ''.join( s)
        if len( s) > STRINGLEN : 
            self.mark( 'string too long') 
        self.next()
        self.value = s[:STRINGLEN]
        return Lex.string_

    def getHexString( self):
        self.next();
        self.value = ''
        while (self.ch != '') and (self.ch != '$') :
            while self.ch in  ' \x09\x0D': self.next()   # skip blanks
            s = self.ch; self.next()
            s += self.ch; self.next()
            try:   m = int( s, base = 16)
            except ValueError:
                self.mark( 'hex dig pair expected')
            if len( self.value) < STRINGLEN : 
                self.value += chr( m); 
            else: self.mark( 'string too long') 
        self.next()
        return Lex.string_

    def  Ten( self, e): # returns a REAL;
        x = 1.0 
        t = 10.0
        while e > 0 :
            if  e & 1 : x *= t  
            t = t * t; 
            e >>= 1
        return x
  
    def getNumber( self):  # returns a tuple (char_/integer_/real_ , ival/rval)
        self.value = 0
        digits = []
        while self.ch in string.hexdigits:
            digits.append( self.ch)
            self.next()
        if len(digits) > 16 : self.mark( 'too many digits'); s = ''
        else: s = ''.join( digits)
        # print s # dbg

        if (self.ch in 'XHR') :  # hex (char, int or real)
            c = self.ch; self.next()
            try: self.value = int( s, base=16)
            except ValueError: self.mark( 'bad hex digits')
            if c  == 'X': 
                if self.value >= 0x100 :  self.mark( 'bad char value')
                return  Lex.char_
            elif c == 'R' : 
                self.value *= 1.0
                return Lex.real_
            else:   # 'H' 
                return Lex.int_

        elif self.ch == "." : 
            self.next();
            if self.ch == "." :     
                self.ch = chr(0x7f)  # double dot (upto) -> decimal integer
                try: self.value = int( s, base=10)
                except ValueError: self.mark( 'bad integer')
                return  Lex.int_

            else:     # real numbers
                x = 0.0
                e = 0
                try: x = int( s, base=10)
                except ValueError: self.mark( 'bad integer part')
                while self.ch in string.digits :  # fraction
                    x = x * 10.0 + int( self.ch); 
                    e -= 1 
                    self.next()
                
                if self.ch in 'ED' :  # scale factor
                    self.next()
                    s = 0
                    if self.ch == '-' : 
                        negE = True
                        self.next()
                    else: 
                        negE = False
                        if self.ch == '+' : self.next() 
                    if  self.ch in string.digits :
                        while True: 
                            s = s * 10 + int(self.ch) 
                            self.next()
                            if not self.ch in string.digits: break
                        e = (e - s) if negE else (e + s) 
                    else: self.mark( 'digit?')
                  
                if e < 0 :
                    x = x / self.Ten(-e) if e >= -MAXEX else 0.0 
                elif e > 0 :
                    if e <= MAXEX : x = self.Ten(e) * x 
                    else:  x = 0.0; self.mark( 'too large')
                self.value = x
                return  Lex.real

        else:   # decimal integer
            try: self.value = int( ''.join( digits)) 
            except ValueError : self.mark( 'bad integer')
            return Lex.int_

    def comment( self):
        self.next();
        while True:
            while (self.ch != '') and (self.ch != '*'): 
                if self.ch == "(" : 
                    self.next()        # nested comments
                    if self.ch == '*' : self.comment() 
                else: self.next()
            while self.ch == "*" : self.next() 
            if self.ch == ')' or self.ch == '' : break
        if self.ch != '' : self.next() 
        else: self.mark( 'unterminated comment')

    def get( self):   # returns last symbol detected 
        self.value = None
        while ( self.ch != '') and ( self.ch <= ' ') : self.next()
        if self.ch == '': return Lex.eof_
        if self.ch < 'A' :
            if self.ch < '0' :
                if   self.ch == '"' : return self.getString()
                elif self.ch == "#" : self.next(); return Lex.neq
                elif self.ch == "$" : return self.getHexString() 
                elif self.ch == "&" : self.next(); return Lex.and_
                elif self.ch == "(" : 
                    self.next(); 
                    if self.ch == "*" : return self.comment()
                    else: return Lex.lparen
                elif self.ch == ")" : self.next(); return Lex.rparen
                elif self.ch == "*" : self.next(); return Lex.times
                elif self.ch == "+" : self.next(); return Lex.plus
                elif self.ch == "," : self.next(); return Lex.comma
                elif self.ch == "-" : self.next(); return Lex.minus
                elif self.ch == "." : 
                    self.next();
                    if self.ch == "." : self.next(); return Lex.upto
                    else: return Lex.period
                elif self.ch == "/" : self.next(); return Lex.rdiv
                else: self.next();  return Lex.null   # ! % ' 
                
            elif self.ch < ":" : return self.getNumber()
            elif self.ch == ":" : 
                self.next();
                if self.ch == "=" : self.next(); return Lex.becomes
                else: return Lex.colon
            elif self.ch == ";" : self.next(); return Lex.semicolon
            elif self.ch == "<" :  
                self.next();
                if self.ch == "=" : self.next(); return Lex.leq
                else: return Lex.lss
            elif self.ch == "=" : self.next(); return Lex.eql
            elif self.ch == ">" : 
                self.next();
                if self.ch == "=" : self.next(); return Lex.geq
                else: return Lex.gtr
            else:  self.next(); return Lex.null

        elif self.ch < "[" : return self.getIdentifier()
        elif self.ch < "a" :
            c = self.ch; self.next()
            if   c == "[" : return Lex.lbrak
            elif c == "]" : return Lex.rbrak
            elif c == "^" : return Lex.arrow
            else:  return Lex.null         # _ ` 

        elif self.ch < "{" : return self.getIdentifier() 
        else:
            c = self.ch; self.next()
            if   c == "{" : return Lex.lbrace
            elif c == "}" : return Lex.rbrace
            elif c == "|" : return Lex.bar
            elif c == "~" : return Lex.not_
            elif c == 0x7f: return Lex.upto
            else: return Lex.null
            

