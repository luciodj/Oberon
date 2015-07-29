#!/opt/local/bin/python
""" 
    MODULE ORS; (* NW 19.9.93 / 1.4.2014  Scanner in Oberon-07*)
    I MPORT SYSTEM, Texts, Oberon;

    Oberon Scanner does lexical analysis. Input is Oberon-Text, output is
    sequence of symbols, i.e identifiers, numbers, strings, and special symbols.
    Recognises all Oberon keywords and skips comments. The keywords are
    recorded in a table.
    Get(sym) delivers self.next symbol from input text with Reader R.
    Mark(msg) records error and delivers error message with Writer W.
    If Get delivers ident, then the identifier (a string) is in variable id, if int or char
    in ival, if real in rval, and if string in str (and slen) 
"""
import sys
import string
 
IdLen = 32
maxExp = 38
stringBufSize = 256
  
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
    var_ = 65; procedure_ = 66; begin_ = 67; import_ = 68; module_ = 69;

class Lexer:
    def __init__( self, infile, pos):
        infile.seek( pos)
        self.infile = infile
        self.ch = infile.read(1); 
        # dbg # print self.ch,
        self.errpos = pos 
        self.errcnt = 0
        # return values
        self.sym = Lex.null_
        self.ival = 0
        self.rval = 0
        self.id = ''
        self.strval = ''

    def next( self):                    # get next character 
        self.ch = self.infile.read(1)
        print self.ch,

    def mark( self, msg):
        p = self.infile.tell()
        if p > self.errpos and  self.errcnt < 25:
            print "  pos ", p, " ", msg  # append(Oberon.Log, W.buf)
        self.errcnt += 1 
        self.errpos = p + 4

    def getIdentifier( self):  # returns sym = keyword or ident
        self.sym = Lex.ident_
        self.id = ''
        for i in xrange( IdLen):
            self.id += self.ch
            self.next()
            if  not self.ch.isalnum(): break
        if self.id in KeyTable : 
            self.sym = KeyTable[ self.id] 

    def getString( self):
        self.sym = Lex.string_
        self.next()
        self.strval = ''
        for i in xrange( stringBufSize):
            if (self.ch == '') or (self.ch == '"') : break
            if self.ch in string.printable :
                self.strval += self.ch
            if i == stringBufSize-1 : 
                self.mark( 'string too long')
                break
            self.next()
        self.next()

    def getHexString( self):
        self.sym = Lex.string_
        print "hexstring"
        self.strval = ''
        self.next();
        while (self.ch != '') and (self.ch != '$') :
            while (self.ch == ' ') or (self.ch == 0x9) or (self.ch == 0x0D) : self.next()   # skip
            if ( '0' <= self.ch) and (self.ch <= '9') : m = int( self.ch)
            elif ('A' <= self.ch) and (self.ch <= 'F') : m = ord( self.ch) - 0x37
            else: 
                m = 0; self.mark( 'hexdig expected')
            self.next();
            if ('0' <= self.ch) & (self.ch <= '9') : n = ord(self.ch) - 0x30
            elif ('A' <= self.ch) & (self.ch <= 'F') : n = ord(self.ch) - 0x37
            else: 
                n = 0; self.mark( 'hexdig expected')
            self.next()
            if len(self.strval) < stringBufSize : 
                self.strval += chr( m * 0x10 + n); 
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
  
    def getNumber( self):  # returns an sym and  ival/rval
        self.ival = 0
        k = 0
        digits = []
        for i in xrange( 16):
            digits.append( string.hexdigits.index( self.ch.lower()))
            self.next()
            if ( not self.ch in string.hexdigits): break 
            elif i == 15 :
                self.mark( 'too many digits')
                digits = [] 
        print digits

        if (self.ch == "H") or (self.ch == "R") or (self.ch == "X") :  # hex (char, int or real)
            for d in digits:
                k = k * 0x10 + d       # no overflow check
            if self.ch == 'X': 
                self.sym = Lex.char_
                if k < 0x100 : self.ival = k 
                else: self.mark( 'illegal value')
            elif self.ch ==  'R' : 
                self.sym = Lex.real_ 
                self.rval = 1.0 *  k
            else: 
                self.sym = Lex.int_
                self.ival = k
            self.next()

        elif self.ch == "." :
            self.next();
            if self.ch == "." : 
                self.ch = chr(0x7f)  # double dot (upto) -> decimal integer
                for d in digits:
                    if d < 10 :
                        if k <= (sys.maxint - d) / 10 : k  = k * 10 + d 
                        else: 
                            self.mark( 'too large')
                            k = 0 
                    else: 
                        self.mark( 'bad integer')
                self.sym = Lex.int_
                self.ival = k

            else:     # real numbers
                x = 0.0
                e = 0
                for d in digits:  # integer part
                    x = x * 10.0 + d

                while self.ch in string.digits :  # fraction
                    x = x * 10.0 + int( self.ch); 
                    e -= 1 
                    self.next()
                
                if (self.ch == 'E') or (self.ch == 'D') :  # scale factor
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
                    x = x / self.Ten(-e) if e >= -maxExp else 0.0 
                elif e > 0 :
                    if e <= maxExp : x = self.Ten(e) * x 
                    else:  x = 0.0; self.mark( 'too large')
                self.sym = Lex.real_
                self.rval = x

        else:   # decimal integer
            for d in digits:
                if d < 10 :
                    if k <= (sys.maxint - int(d)) / 10 : 
                        k = k * 10 + d 
                    else: 
                        self.mark( 'too large'); 
                        k = 0 
                else: 
                    self.mark( 'bad integer')
            self.sym = Lex.int_ 
            self.ival = k

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
        else:
            self.mark( "unterminated comment")

    def get( self):   # returns last symbol detected 
        while ( self.ch != '') and ( self.ch <= ' ') : self.next(); print (self.ch) 
        if self.ch == '': break     # file terminated
        if self.ch < 'A' :
            if self.ch < '0' :
                if   self.ch == '"' : self.getString()
                elif self.ch == "#" : self.next(); self.sym = Lex.neq_
                elif self.ch == "$" : self.getHexString() 
                elif self.ch == "&" : self.next(); self.sym = Lex.and_
                elif self.ch == "(" : 
                    self.next(); 
                    if self.ch == "*" : self.sym = Lex.null_; self.comment()
                    else: self.sym = Lex.lparen_
                elif self.ch == ")" : self.next(); self.sym = Lex.rparen_
                elif self.ch == "*" : self.next(); self.sym = Lex.times_
                elif self.ch == "+" : self.next(); self.sym = Lex.plus_
                elif self.ch == "," : self.next(); self.sym = Lex.comma_
                elif self.ch == "-" : self.next(); self.sym = Lex.minus_
                elif self.ch == "." : 
                    self.next();
                    if self.ch == "." : self.next(); self.sym = Lex.upto_ 
                    else: self.sym = Lex.period_
                elif self.ch == "/" : self.next(); self.sym = Lex.rdiv_
                else: self.next();  self.sym = Lex.null_   # ! % ' 
                
            elif self.ch < ":" : self.getNumber()
            elif self.ch == ":" : 
                self.next();
                if self.ch == "=" : self.next(); self.sym = Lex.becomes_
                else: self.sym = Lex.colon_ 
            elif self.ch == ";" : self.next(); self.sym = Lex.semicolon_
            elif self.ch == "<" :  
                self.next();
                if self.ch == "=" : self.next(); self.sym = Lex.leq_ 
                else: self.sym = Lex.lss_ 
            elif self.ch == "=" : self.next(); self.sym = Lex.eql_
            elif self.ch == ">" : 
                self.next();
                if self.ch == "=" : self.next(); self.sym = Lex.geq_ 
                else: self.sym = Lex.gtr_ 
            else:  self.next(); self.sym = Lex.null_

        elif self.ch < "[" : self.getIdentifier()
        elif self.ch < "a" :
            if   self.ch == "[" : self.sym = Lex.lbrak_
            elif self.ch == "]" :  self.sym = Lex.rbrak_
            elif self.ch == "^" : self.sym = Lex.arrow_
            else:  self.sym = Lex.null_         # _ ` 
            self.next()

        elif self.ch < "{" : self.getIdentifier() 
        else:
            if   self.ch == "{" : self.sym = Lex.lbrace_
            elif self.ch == "}" : self.sym = Lex.rbrace_
            elif self.ch == "|" : self.sym = Lex.bar_
            elif self.ch == "~" : self.sym = Lex.not_
            elif self.ch == 0x7f: self.sym = Lex.upto_
            else: self.sym = Lex.null_
            self.next()


#Texts.OpenWriter(W); 
KeyTable = {  'IF': Lex.if_, 'DO' : Lex.do_, 'OF': Lex.of_,  'OR': Lex.or_, 'TO': Lex.to_, 
              'IN': Lex.in_, 'IS': Lex.is_, 'BY': Lex.by_, 
              'END': Lex.end_, 'NIL': Lex.nil_, 'VAR': Lex.var_, 'DIV': Lex.div_, 'MOD': Lex.mod_, 
              'FOR': Lex.for_, 'ELSE': Lex.else_, 'THEN': Lex.then_, 'TRUE': Lex.true_, 'TYPE': Lex.type_, 
              'CASE': Lex.case_, 'ELSIF': Lex.elsif_, 'FALSE': Lex.false_, 'ARRAY': Lex.array_, 
              'BEGIN': Lex.begin_, 'CONST': Lex.const_, 'UNTIL': Lex.until_, 'WHILE': Lex.while_, 
              'RECORD': Lex.record_, 'REPEAT': Lex.repeat_, 'RETURN': Lex.return_, 'IMPORT': Lex.import_, 
              'MODULE': Lex.module_, 'POINTER': Lex.pointer_, 'PROCEDURE': Lex.procedure_
              }
