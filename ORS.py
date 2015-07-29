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
  
class Lex:    # lexical symbols
    null_ = 0; times_ = 1; rdiv_ = 2; div_ = 3; mod_ = 4;
    and_ = 5; plus_ = 6; minus_ = 7; or_ = 8; eql_ = 9;
    neq_ = 10; lss_ = 11; leq_ = 12; gtr_ = 13; geq_ = 14;
    in_ = 15; is_ = 16; arrow_ = 17; period_ = 18;
    char_ = 20; int_ = 21; real_ = 22; false_ = 23; true_ = 24;
    nil_ = 25; string_ = 26; not_ = 27; lparen_ = 28; lbrak_ = 29;
    lbrace_ = 30; ident_ = 31;
    if_ = 32; while_ = 34; repeat_ = 35; case_ = 36; for_ = 37;
    comma_ = 40; colon_ = 41; becomes_ = 42; upto_ = 43; rparen_ = 44;
    rbrak_ = 45; rbrace_ = 46; then_ = 47; of_ = 48; do_ = 49;
    to_ = 50; by_ = 51; semicolon_ = 52; end_ = 53; bar_ = 54;
    else_ = 55; elsif_ = 56; until_ = 57; return_ = 58;
    array_ = 60; record_ = 61; pointer_ = 62; const_ = 63; type_ = 64;
    var_ = 65; procedure_ = 66; begin_ = 67; import_ = 68; module_ = 69; eof_ = 70

KeyTable = {  'IF': Lex.if_, 'DO' : Lex.do_, 'OF': Lex.of_,  'OR': Lex.or_, 'TO': Lex.to_, 
              'IN': Lex.in_, 'IS': Lex.is_, 'BY': Lex.by_, 
              'END': Lex.end_, 'NIL': Lex.nil_, 'VAR': Lex.var_, 'DIV': Lex.div_, 'MOD': Lex.mod_, 
              'FOR': Lex.for_, 'ELSE': Lex.else_, 'THEN': Lex.then_, 'TRUE': Lex.true_, 'TYPE': Lex.type_, 
              'CASE': Lex.case_, 'ELSIF': Lex.elsif_, 'FALSE': Lex.false_, 'ARRAY': Lex.array_, 
              'BEGIN': Lex.begin_, 'CONST': Lex.const_, 'UNTIL': Lex.until_, 'WHILE': Lex.while_, 
              'RECORD': Lex.record_, 'REPEAT': Lex.repeat_, 'RETURN': Lex.return_, 'IMPORT': Lex.import_, 
              'MODULE': Lex.module_, 'POINTER': Lex.pointer_, 'PROCEDURE': Lex.procedure_
              }

class Lexer:
    def __init__( self, reader):
        self.reader = reader    
        self.ch = reader.next()
        # print self.ch, # dbg
        self.pos = 0 
        self.errpos = 0
        self.errcnt = 0

    def next( self):                    # get next character 
        # self.ch = self.infile.read(1)
        try: self.ch = self.reader.next()
        except StopIteration: self.ch = ''
        # print self.ch,  # dbg

    def mark( self, msg):
        p = self.infile.tell()
        if p > self.errpos and  self.errcnt < 25:
            print " pos", p, msg  
        self.errcnt += 1 
        self.errpos = p + 4

    def getIdentifier( self):           # returns sym = keyword or ident
        ids = []
        while self.ch.isalnum() :
            ids.append( self.ch)
            self.next()
        ids = ''.join( ids)
        if ids in KeyTable : return( KeyTable[ ids], None)
        else: return ( Lex.ident_, ids[: IDLEN])

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
        return Lex.string_, s[:STRINGLEN]

    def getHexString( self):
        self.sym = Lex.string_
        self.strval = ''
        self.next();
        while (self.ch != '') and (self.ch != '$') :
            while self.ch in  ' \x09\x0D': self.next()   # skip blanks
            s = self.ch; self.next()
            s += self.ch; self.next()
            try:   m = int( s, base = 16)
            except ValueError:
                self.mark( 'hex dig pair expected')
            if len(self.strval) < STRINGLEN : 
                self.strval += chr( m); 
            else: self.mark( 'string too long') 
        self.next(); 

    def  Ten( self, e): # returns a REAL;
        x = 1.0 
        t = 10.0
        while e > 0 :
            if  e & 1 : x *= t  
            t = t * t; 
            e >>= 1
        return x
  
    def getNumber( self):  # returns a tuple (char_/integer_/real_ , ival/rval)
        digits = []
        while self.ch in string.hexdigits:
            digits.append( self.ch)
            self.next()
        if len(digits) > 16 : self.mark( 'too many digits'); s = ''
        else: s = ''.join( digits)
        # print s # dbg

        if (self.ch in 'XHR') :  # hex (char, int or real)
            c = self.ch; self.next()
            try: k = int( s, base=16)
            except ValueError: self.mark( 'bad hex digits')
            if c  == 'X': 
                if k >= 0x100 :  k = 0; self.mark( 'bad char value')
                return  Lex.char_, k
            elif c == 'R' :
                return Lex.real_, 1.0 *  k
            else:   # 'H' 
                return Lex.int_, k

        elif self.ch == "." : 
            self.next();
            if self.ch == "." :     
                self.ch = chr(0x7f)  # double dot (upto) -> decimal integer
                try: k = int( s, base=10)
                except ValueError: self.mark( 'bad integer')
                return  Lex.int_, k

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
                return  Lex.real_, x

        else:   # decimal integer
            try: k = int( ''.join( digits)) 
            except ValueError : self.mark( 'bad integer')
            return Lex.int_, k

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
        else: self.mark( "unterminated comment")

    def get( self):   # returns last symbol detected 
        while ( self.ch != '') and ( self.ch <= ' ') : self.next()
        if self.ch == '': return( Lex.eof_, None)
        if self.ch < 'A' :
            if self.ch < '0' :
                if   self.ch == '"' : return self.getString()
                elif self.ch == "#" : self.next(); return( Lex.neq_, None)
                elif self.ch == "$" : return self.getHexString() 
                elif self.ch == "&" : self.next(); return( Lex.and_, None)
                elif self.ch == "(" : 
                    self.next(); 
                    if self.ch == "*" : return self.comment()
                    else: return( Lex.lparen_, None)
                elif self.ch == ")" : self.next(); return( Lex.rparen_, None)
                elif self.ch == "*" : self.next(); return( Lex.times_, None)
                elif self.ch == "+" : self.next(); return( Lex.plus_, None)
                elif self.ch == "," : self.next(); return( Lex.comma_, None)
                elif self.ch == "-" : self.next(); return( Lex.minus_, None)
                elif self.ch == "." : 
                    self.next();
                    if self.ch == "." : self.next(); return( Lex.upto_, None)
                    else: return (Lex.period_, None)
                elif self.ch == "/" : self.next(); return( Lex.rdiv_, None)
                else: self.next();  return( Lex.null_, None)   # ! % ' 
                
            elif self.ch < ":" : return self.getNumber()
            elif self.ch == ":" : 
                self.next();
                if self.ch == "=" : self.next(); return( Lex.becomes_, None)
                else: return( Lex.colon_, None)
            elif self.ch == ";" : self.next(); return( Lex.semicolon_, None)
            elif self.ch == "<" :  
                self.next();
                if self.ch == "=" : self.next(); return( Lex.leq_, None)
                else: return( Lex.lss_, None)
            elif self.ch == "=" : self.next(); return( Lex.eql_, None)
            elif self.ch == ">" : 
                self.next();
                if self.ch == "=" : self.next(); return( Lex.geq_, None)
                else: return( Lex.gtr_, None) 
            else:  self.next(); return( Lex.null_, None)

        elif self.ch < "[" : return self.getIdentifier()
        elif self.ch < "a" :
            c = self.ch; self.next()
            if   c == "[" : return( Lex.lbrak_, None)
            elif c == "]" : return( Lex.rbrak_, None)
            elif c == "^" : return( Lex.arrow_, None)
            else:  return( Lex.null_, None)         # _ ` 

        elif self.ch < "{" : return self.getIdentifier() 
        else:
            c = self.ch; self.next()
            if   c == "{" : return( Lex.lbrace_, None)
            elif c == "}" : return( Lex.rbrace_, None)
            elif c == "|" : return( Lex.bar_, None)
            elif c == "~" : return( Lex.not_, None)
            elif c == 0x7f: return( Lex.upto_, None)
            else: return( Lex.null_, None)
            

