#!/usr/bin/env python
'''
  MODULE OSG; #  NW 19.12.94 / 20.10.07 / 26.10.2013*) 
  IMPORT SYSTEM, Files, Texts, Oberon, oss, RISC;
'''
import risc, oss
from collections import namedtuple

MemSize = 8192
WordSize = 4

class eClass:
    strings = [ 'Const', 'Var', 'Par', 'Field', 'Type', 'SProc', 'SFunc', 'Proc', 'NoTyp']
    Const, Var, Par, Field, Typ, SProc, SFunc, Proc, NoTyp = range( 9)

class eMode:
    Reg, RegI, Cond = range( 3)

# reserved registers
SB = 13; SP = 14; LNK = 15;   

class eForm: # forms enum
    Boolean, Integer, Array, Record = range( 4)

U = 0x2000
# frequently used opcodes
Mov = 0; Lsl = 1; Asr = 2; Ror= 3; And = 4; Ann = 5; Ior = 6; Xor = 7
Add = 8; Sub = 9; Cmp = 9; Mul = 10; Div = 11
Ldw = 0; Stw = 2
BR = 0; BLR = 1; BC = 2; BL = 3
MI = 0; PL = 8; EQ = 1; NE = 9; LT = 5; GE = 13; LE = 6; GT = 14

class Item:
    def __init__( self, mode=eMode.Reg, level=0, type=None):
        self.mode = mode
        self.lev = level  # int
        self.type = None # Type Descriptor
        self.a = 0    # int
        self.b = 0    # int
        self.r = 0    # int

ObjScope = namedtuple( 'ObjScope', [
    'name',
    'idents', # list of ObjDesc
    ])

class ObjDesc :
    def __init__( self, name='', cl=eClass.Const):
        self.name = name
        self.class_ =  cl   # enum eClass
        self.lev = 0        # integer
        # self.idents = []    # list of Ident
        self.type = None    # TypeDesc obj
        self.value = 0 
        self.nofpar = 0
    
    def __repr__( self):
        return 'ObjDesc %s: %s value=%s, nofpar=%s, type=%s\n\r' % \
                ( self.name, eClass.strings[self.class_], self.value, self.nofpar, self.type)

class TypeDesc:
    def __init__( self, name='', form=eForm.Integer, size=4):
        self.name = name
        self.form = form     # enum eForm
        self.size = size     # of bytes
        self.base = None     # parent type (array)
        self.nofpar = 0      # number of parameters (function)
        self.len = 0         # number of elements (array)
    def __repr__( self):
        return 'TypeDesc %s: form=%s, size=%s, base=%s, nofpar=%s' % \
                ( self.name, self.form, self.size, self.base, self.nofpar)
    

class Osg:  
    curlev = 0
    pc = 0
    entry = 0
    fixlist = 0
    rh = 0    # register stack pointer
    relmap = [ EQ, NE, LT, LE, GT, GE]
    # for decoder
    mnemo0 = { Mov : "MOV", Lsl : "LSL", Asr : "ASR", Ror : "ROR", And : "AND", Ann : "ANN", 
             Ior : "IOR", Xor : "XOR", Add : "ADD", Sub : "SUB", Mul : "MUL", Div : "/" }
    mnemo1 = { PL : 'PL', MI : 'MI', EQ : 'EQ', NE : 'NE', LT : 'LT', GE : 'GE', LE : 'LE', GT : 'GT', 15 : 'NO'}
    code = [ 0 for x in xrange( MemSize)] 

    def Put0( self, op, a, b, c):           
        ' emit format-0 instruction'
        code[ self.pc] = (( a * 0x10 + b) * 0x10 + op) * 0x10000 + c
        self.pc += 1

    def Put1( self, op, a, b, im):   
        'emit format-1 instruction'
        if im < 0 : op |= 0x1000    # set v-bit
        self.code[self.pc] = ((( 0x40 + a) * 0x10 + b) * 0x10 + op) * 0x10000 + (im % 0x10000)
        self.pc += 1

    def Put2( self, op, a, b, off):   
        'emit load/store instruction'
        self.code[ self.pc] = ((( 0x08 + op) * 0x10 + a) * 0x10 + b) * 0x100000 + (off % 0x10000) 
        self.pc += 1

    def Put3( self, op, cond, off): 
        'emit branch instruction'
        self.code[ self.pc] = ((0x0C | op) * 0x10 | cond) * 0x1000000 | (off & 0xFFFFF) 
        self.pc += 1

    def incR( self):
        if self.rh < SB : self.rh += 1 
        else: oss.mark("register stack overflow") 

    def CheckRegs( self):
        if self.rh != 0 :
            # Texts.WriteString(W, "RegStack!"); Texts.WriteInt(W, R, 4);
            # print
            oss.mark( 'Reg Stack: %d' % self.rh); self.rh = 0

    def SetCC( self, x, n): 
        x.mode = Cond; x.a = 0; x.b = 0; x.r = n

    def testRange( self, x): 
        '16-bit entity'
        if ( x > 0xFFFF) or (x < - 0x10000) : oss.mark( "value too large")

    def negated( self, cond):
        cond += 8 if cond < 8 else -8 
        return cond

    def fix( self, at, _with): 
        self.code[ at] = self.code[ at] / 0x1000000 * 0x1000000 + (_with % 0x1000000)

    def fixLink( self, L): 
        while L != 0 :
            if L < MemSize : 
                L1 = self.code[ L] % 0x40000
                fix( self, at=L, _with=pc-L-1)
                L = L1 
  
    def load( self, x): # ( x:item) -> item
        'emits load of an item in a register'
        if x.mode != eMode.Reg :
            if x.mode == Var :
                if x.r > 0 : # local
                    self.Put2( Ldw, self.rh, SP, x.a) 
                else:   # global 
                    self.Put2( Ldw, self.rh, SB, x.a) 
                x.r = self.rh; self.incR()
            elif x.mode == Par : 
                self.Put2( Ldw, self.rh, x.r, x.a); 
                self.Put2( Ldw, self.rh, self.rh, 0); 
                x.r = self.rh; self.incR()
            elif x.mode == Const :
                if (x.a >= 0x10000) or (x.a < -0x10000) : oss.mark( 'const too large') 
                self.Put1( Mov, self.rh, 0, x.a) 
                x.r = self.rh; self.incR(); print 'load inc', self.rh 
            elif x.mode == eMode.RegI : self.Put2( Ldw, x.r, x.r, x.a)
            elif x.mode == eMode.Cond :
                self.Put3( 2, self.negated( x.r), 2);
                self.FixLink( x.b); self.self.Put1( Mov, self.rh, 0, 1); self.Put3(2, 7, 1);
                self.FixLink( x.a); self.self.Put1( Mov, self.rh, 0, 0); 
                x.r = self.rh; self.incR()        
            x.mode = eMode.Reg
            return x

    def loadAdr( self, x): # ( x: Item) -> Item
        'emits load of the address of an item'
        if x.mode == Var :
            if x.r > 0 : # local
                self.Put1(Add, self.rh, SP, x.a); 
                x.r = self.rh 
            else:   # global
                self.Put1(Add, self.rh, SB, x.a) 
            self.incR()
        elif x.mode == Par: 
            self.Put2(Ldw, self.rh, SP, x.a); 
            self.Put1(Add, self.rh, self.rh, x.b); 
            x.r = self.rh; self.incR()
        elif (x.mode == RegI) & (x.a != 0) : 
            self.Put1(Add, x.r, x.r, x.a)
        else: oss.mark( 'address error')         
        x.mode = Reg
        return x

    def loadCond( self, x): # ( x:Item) -> Item
        'emits load of a boolean item'
        if x.type.form == Boolean :
            if x.mode == Const : 
                x.r = 15 - x.a * 8 
            else: 
                x = load(x); 
                self.Put1( Cmp, x.r, x.r, 0)
                x.r = NE; self.rh -= 1
            x.mode = Cond; x.a = 0; x.b = 0
        else: oss.mark("not Boolean")
        return x

    def merged( self, L0, L1): # (l0, l1: LONGINT): LONGINT 
        if L0 != 0 :
            L3 = L0
            while True: 
                L2 = L3
                L3 = self.code[ L2] % 0x40000 
                if L3 == 0: break
            self.code[ L2] = self.code[ L2] + L1
            L1 = L0        
        return L1

  # -----------------------------------------------

    def IncLevel( self, n): 
        self.curlev = self.curlev + n

    def MakeConstItem( self, x, type, value): 
        'make item x a constant value'
        x.class_ = eClass.Const
        x.type = type
        x.a = value

    def MakeItem( self, x, y, curlev): # ( y: Object; curlev) -> item
        'make an item out of an object'
        x.mode = y.class_; x.type = y.type; x.a = y.value; x.r = y.lev;
        if y.class_ == eClass.Par : x.b = 0 
        if (y.lev > 0) & (y.lev != curlev) & (y.class_ != eClass.Const) : oss.mark( 'level error') 
        return x

    def Field( self, x, y): # x:Item y:Object
        'x = x.y'
        if (x.mode == Var) or (x.mode == RegI) : 
          x.a = x.a + y.val
        elif x.mode == Par : 
            self.Put2( Ldw, self.rh, x.r, x.a)
            x.mode = RegI; 
            x.r = self.rh; 
            x.a = y.val; self.incR()
        return x, y

    def Index( self, x, y): # x:Item y:Object
        'x = x[y]'
        if y.mode == Const :
            if (y.a < 0) or (y.a >= x.type.len) : oss.mark("bad index") 
            if x.mode == Par : 
                self.Put2( Ldw, self.rh, x.r, x.a); 
                x.mode = RegI; 
                x.a = 0 
            x.a = x.a + y.a * x.type.base.size
        else: 
            s = x.type.base.size
            if y.mode != Reg : 
                self.load(y) 
                if s == 4 : self.Put1( Lsl, y.r, y.r, 2) 
                else: self.Put1( Mul, y.r, y.r, s) 
            if x.mode == Var :
                if x.r > 0 : self.Put0( Add, y.r, SP, y.r) 
                else: self.Put0( Add, y.r, SB, y.r) 
                x.mode = RegI; 
                x.r = y.r
            elif x.mode == Par :
                self.Put2( Ldw, self.rh, SP, x.a); 
                self.Put0( Add, y.r, self.rh, y.r); 
                x.mode = RegI; 
                x.r = y.r
            elif x.mode == RegI : 
                self.Put0( Add, x.r, x.r, y.r); 
                self.rh -= 1
        return x

    #  Code generation for Boolean operators 

    def Not( self, x): 
        'x = ~x'
        if x.mode != Cond : self.loadCond(x) 
        x.r = negated(x.r); t = x.a; x.a = x.b; x.b = t
        return x

    def And1( self, x):
        'x = x and '
        if x.mode != Cond : self.loadCond( x) 
        self.Put3(BC, negated(x.r), x.a); x.a = pc-1; FixLink(x.b); x.b = 0
        return x

    def And2( self, x, y): 
        ' x = x and y'
        if y.mode != Cond : self.loadCond(y) 
        x.a = merged(y.a, x.a); x.b = y.b; x.r = y.r
        return x

    def Or1( self, x): 
        'x = x or'
        if x.mode != Cond : self.loadCond(x) 
        self.Put3(BC, x.r, x.b);  x.b = pc-1; FixLink(x.a); x.a = 0
        return x

    def Or2( self, x, y):
        'x = x or y'
        if y.mode != Cond : self.loadCond(y) 
        x.a = y.a; 
        x.b = merged(y.b, x.b); 
        x.r = y.r
        return x

    #  Code generation for arithmetic operators 

    def Neg( self, x):
        'x = -x'
        if x.mode == Const : 
            x.a = -x.a
        else: 
            self.load( x)
            self.Put1( Mov, self.rh, 0, 0) 
            self.Put0( Sub, x.r, self.rh, x.r)
        return x

    def AddOp( self, op): 
        'x = x +/- y'
        if op == oss.plus :
            if (x.mode == Const) & (y.mode == Const) : 
                x.a = x.a + y.a
            elif y.mode == Const : 
                self.load( x);
                if y.a != 0 : 
                    self.Put1( Add, x.r, x.r, y.a) 
            else: 
                self.load( x); self.load( y); 
                self.Put0( Add, self.rh-2, x.r, y.r)
                self.rh -= 1; x.r = self.rh-1
        else: # op = oss.minus
            if (x.mode == Const) & (y.mode == Const) : 
                x.a = x.a - y.a
            elif y.mode == Const : 
                self.load( x);
                if y.a != 0 :
                   self.Put1( Sub, x.r, x.r, y.a) 
            else: 
                self.load( x); self.load( y)
                self.Put0( Sub, self.rh-2, x.r, y.r)
                self.rh -= 1; x.r = self.rh-1

    def MulOp( self, x, y): #Item);   
        'x = x * y'
        if (x.mode == Const) & (y.mode == Const) : 
            x.a = x.a * y.a
        elif (y.mode == Const) & (y.a == 2) : 
            self.load(x)
            self.Put1( Lsl, x.r, x.r, 1)
        elif y.mode == Const : 
            self.load(x)
            self.Put1( Mul, x.r, x.r, y.a)
        elif x.mode == Const : 
            self.load(y)
            self.Put1( Mul, y.r, y.r, x.a)
            x.mode = Reg; x.r = y.r
        else: 
            self.load( x); self.load( y); 
            self.Put0( Mul, self.rh-2, x.r, y.r)
            self.rh -= 1; x.r = self.rh-1

    def DivOp(self, op, x, y): #( LONGINT; VAR x, y: Item);   #  x = x op y *)
        if op == oss.div :
            if (x.mode == Const) & (y.mode == Const) :
              if y.a > 0 : x.a = x.a / y.a 
              else: oss.mark( 'bad divisor') 
            elif (y.mode == Const) & (y.a == 2) : 
                self.load( x); 
                self.Put1( Asr, x.r, x.r, 1)
            elif y.mode == Const :
                if y.a > 0 : 
                    self.load( x)
                    self.Put1( Div, x.r, x.r, y.a) 
                else: oss.mark( 'bad divisor') 
            else: 
                  self.load( y); self.load( x)
                  self.Put0( Div, self.rh-2, x.r, y.r)
                  self.rh -= 1; x.r = self.rh-1
        else:   # op = oss.mod
            if (x.mode == Const) & (y.mode == Const) :
                if y.a > 0 : x.a = x.a % y.a 
                else: oss.mark( 'bad modulus') 
            elif (y.mode == Const) & (y.a == 2) : 
                self.load( x)
                self.Put1( And, x.r, x.r, 1)
            elif y.mode == Const :
                if y.a > 0 : 
                      self.load( x); 
                      self.Put1( Div, x.r, x.r, y.a); 
                      self.Put0( Mov+U, x.r, 0, 0) 
                else: oss.mark( 'bad modulus') 
            else: 
                self.load( y); self.load( x)
                self.Put0( Div, self.rh-2, x.r, y.r)
                self.Put0( Mov+U, self.rh-2, 0, 0)
                self.rh -= 1; x.r = self.rh-1
        return x, y

    def Relation( self, op, x, y): 
        'x = x ? y'
        if y.mode == Const : 
            self.load( x)
            self.Put1( Cmp, x.r, x.r, y.a)
            self.rh -= 1
        else: 
            self.load(x); self.load( y)
            self.Put0( Cmp, x.r, x.r, y.r)
            self.rh -= 2 
        self.SetCC( x, self.relmap[op - oss.eql])
        return x, y

    def Store( self, x, y):  #  x <= y 
        self.load( y);
        if x.mode == eClass.Var :
            if x.r > 0 : # local*) 
                self.Put2( Stw, y.r, SP, x.a) 
            else: 
                self.Put2( Stw, y.r, SB, x.a) 
        elif x.mode == Par : 
            self.Put2( Ldw, self.rh, SP, x.a); 
            self.Put2( Stw, y.r, self.rh, x.b)
        elif x.mode == RegI : 
            self.Put2( Stw, y.r, x.r, x.a)
            self.rh -= 1
        else: oss.mark( 'illegal assignment')
        self.rh -= 1
        

    def VarParam( self,  x, ftype): # ( xItem; ftype: Type) -> Item
        xmd = x.mode; loadAdr(x);
        if ( ftype.form == Array) and (ftype.len < 0) : # open array
            if x.type.len >= 0 : 
                self.Put1( Mov, self.rh, 0, x.type.len) 
            else:  
                self.Put2( Ldw, self.rh, SP, x.a+4) 
            self.incR()
        elif ftype.form == Record :
            if xmd == Par : self.Put2( Ldw, self.rh, SP, x.a+4); self.incR() 

    def ValueParam( self, x): # ( x: Item) -> Item
        return self.load(x)

    def OpenArrayParam( self, x):
        self.loadAdr(x);
        if x.type.len >= 0 : 
            self.Put1( Mov, self.rh, 0, x.type.len) 
        else: 
            self.Put2( Ldw, self.rh, SP, x.a+4) 
        self.incR()

  # ---------------------------------*)
  
    def CFJump( self, x): 
        'conditional forward jump'
        if x.mode != Cond : x = self.loadCond(x) 
        self.Put3( 2, self.negated(x.r), x.a); self.FixLink(x.b); x.a = self.pc-1
        return x

    def FJump( self, L): 
        'unconditional forward jump'
        self.Put3( 2, 7, L); L = self.pc-1

    def CBJump( self, x, L):
        'conditional backward jump'
        if x.mode != Cond : x = self.loadCond(x) 
        self.Put3( 2, self.negated(x.r), L- self.pc-1)
        return x
    
    def BJump( self, L): 
        'unconditional backward jump'
        self.Put3( 2, 7, L-self.pc-1)

    def Call( self, obj): # ( obj: Object)
        self.Put3( 3, 7, obj.val - self.pc-1); 
        self.rh = 0

    def Enter( self, parblksize, locblksize): 
        a = 4; r = 0; 
        self.Put1( Sub, SP, SP, locblksize)
        self.Put2( Stw, LNK, SP, 0)
        while a < parblksize : 
            self.Put2( Stw, r, SP, a)
            r += 1
            a += 4 

    def Return( self, size): 
        self.Put2( Ldw, LNK, SP, 0); 
        self.Put1( Add, SP, SP, size); 
        self.Put3( BR, 7, LNK); 
        self.rh = 0

    def Ord( self, x): 
        self.load(x); # x.type = intType
        return x

    def ReadInt( self, x): 
        self.loadAdr( x); 
        self.Put1( Mov, self.rh, 0, -4)
        self.Put2( Ldw, self.rh, self.rh, 0)
        self.Put2( Stw, self.rh, x.r, 0); 
        self.rh -= 1
        return x

    def eot( self, x): 
        self.Put1( Mov, self.rh, 0, -8); self.Put2(Ldw, self.rh, self.rh, 0)
        self.SetCC( x, EQ)
        return x

    def WriteInt( self, x): 
        self.load( x); 
        self.Put1( Mov, self.rh, 0, -4)
        self.Put2( Stw, x.r, self.rh, 0)
        self.rh -= 1
        return x

    def WriteChar( self, x): 
        self.load( x); 
        self.Put1( Mov, self.rh, 0, -8)
        self.Put2( Stw, x.r, self.rh, 0)
        self.rh -= 1
        return x

    def WriteLn( self):
        self.Put1( Mov, self.rh, 0, -12)
        self.Put2( Stw, self.rh, self.rh, 0)

    def Open( self): 
        self.curlev = 0
        self.pc = 0 
        self.rh = 0; 
        self.Put3( 2, 7, 0)

    def Header( self, size): 
        self.entry = self.pc
        self.fix( 0, self.pc-1)

    def Close( self):
        self.Put1( Mov, 0, 0, 0)
        self.Put3( 0, 7, 0)

    # -------------------- output -----------------------

    def WriteReg( self, r):
        if r < 13 :    print "R%d" % r,
        elif r == 13 : print 'SB',
        elif r == 14 : print 'SP',
        elif r == 15 : print 'LNK',
  
    def Decode( self):
        print hex( self.code[ 0]), hex( code[ 1])
        i = 0;
        while i < self.pc :
            w = self.code[ i]
            a = w / 0x1000000 % 0x10
            b = w / 0x100000 % 0x10
            print i, 0x9  #tab
            if (w & 0x80000000)  == 0 :  # ~p:  register instruction
                op = w / 0x10000 % 0x10
                print mnemo0[ op],  
                self.WriteReg( a) 
                self.WriteReg( b)
                if (w & 0x40000000) == 0 : # ~q 
                    WriteReg(w % 0x10) 
                else: 
                    c = w % 0x10000
                    if (w & 0x10000000) != 0: # v sign extends
                        c = c | 0xFFFF0000 
                    print c
            elif (w & 0x40000000) == 0 :  # load/store
                if (w & 20000000) !=0 : print 'STW', 
                else: print 'LDW',
                self.WriteReg( a); 
                self.WriteReg(b); 
                print  w % 0x100000
            else:  # Branch instr
                print 'B',
                if (w & 10000000) != 0 : 
                    print 'L',
                print self.mnemo1[ a]
                if (w & 20000000) == 0: # u?
                    WriteReg(w % 0x10) 
                else:
                    w = w % 0x1000000
                    if w >= 0x800000 : w = w - 0x1000000 
                    print w,          
            print
            i += 1
        print


    def Execute( self):
        risc.run( self.code, self.pc)

