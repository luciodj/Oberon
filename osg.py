#!/usr/bin/env python
'''
  MODULE OSG; #  NW 19.12.94 / 20.10.07 / 26.10.2013*) 

'''
from risc import Risc
from oss import Lex, mark
from collections import namedtuple

MemSize = 8192
WordSize = 4

class eClass:
    strings = [ 'Const', 'Var', 'Par', 'Field', 'Type', 'SProc', 'SFunc', 'Proc', 'NoTyp', 'Reg', 'RegI', 'Cond']
    Const, Var, Par, Field, Type, SProc, SFunc, Proc, NoTyp, Reg, RegI, Cond = range( 12)

# reserved registers
BP = 13; SP = 14; LNK = 15;   

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
    def __init__( self, mode=eClass.Reg, level=0, type=None):
        self.mode = mode
        self.lev = level  # int
        self.type = None # Type Descriptor
        self.a = 0    # int
        self.b = 0    # int
        self.r = 0    # int
    def __repr__( self):
        return 'item: %s  level:%d a:%d b:%d r:%d type:[%s]' % \
                ( eClass.strings[ self.mode], self.lev, self.a, self.b, self.r, self.type)

ObjScope = namedtuple( 'ObjScope', [
    'name',
    'idents', # list of ObjDesc
    ])

class ObjDesc :
    def __init__( self, name='', cl=eClass.Const):
        self.name = name
        self.class_ =  cl   # enum eClass
        self.level = 0        # integer
        self.type = None    # TypeDesc obj
        self.value = 0 
        self.params = None
        self.nofpar = 0
    def __repr__( self):
        return 'ObjDesc %s: %s value=%s, nofpar=%s, type:[%s]\n\r' % \
                ( self.name, eClass.strings[self.class_], self.value, self.nofpar, self.type)

class TypeDesc:
    def __init__( self, name='', form=eForm.Integer, size=4):
        self.name = name
        self.form = form     # enum eForm
        self.size = size     # of bytes
        self.base = None     # parent type (array)
        self.fields= None    # list of fields (record)
        self.nofpar = 0      # number of parameters (function)
        self.len = 0         # number of elements (array)
    def __repr__( self):
        if self.form == eForm.Array:
            return 'TypeDesc %s: form=%s, len=%s, base=%s, size=%s' % \
                    ( self.name, 'Array', self.len, self.base, self.size)
        elif self.form == eForm.Record:
            return 'TypeDesc %s: form=%s, fields=%s, size=%s' % \
                    ( self.name, 'Record', self.fields, self.size)
        else:
            return 'TypeDesc %s: form=%s, size=%s' % \
                    ( self.name, self.form, self.size)
            
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
    mnemo1 = { PL : 'PL', MI : 'MI', EQ : 'EQ', NE : 'NE', LT : 'LT', GE : 'GE', LE : 'LE', GT : 'GT', 7:'A', 15 : 'NO'}
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
        if self.rh < BP : self.rh += 1 
        else: mark("register stack overflow") 

    def checkRegs( self):
        if self.rh != 0 :
            mark( 'Reg Stack: %d' % self.rh); self.rh = 0

    def setCC( self, item, n): 
        item.mode = eClass.Cond; item.a = 0; item.b = 0; item.r = n

    def testRange( self, x): 
        '16-bit entity'
        if ( x > 0xFFFF) or (x < - 0x10000) : mark( "value too large")

    def negated( self, cond):
        cond = cond+8 if cond < 8 else cond-8 
        return cond

    def fix( self, at, _with): 
        self.code[ at] = self.code[ at] / 0x1000000 * 0x1000000 + (_with % 0x1000000)

    def fixLink( self, L): 
        while L != 0 :
            if L < MemSize : 
                L1 = self.code[ L] % 0x40000
                self.fix( at=L, _with = self.pc-L-1)
                L = L1 
  
    def load( self, item): # 
        'emits load of an item in a register'
        if item.mode != eClass.Reg :
            if item.mode == eClass.Var :
                if item.r > 0 : # local
                    self.Put2( Ldw, self.rh, SP, item.a) 
                else:   # global 
                    self.Put2( Ldw, self.rh, BP, item.a) 
                item.r = self.rh; self.incR()
            elif item.mode == eClass.Par : 
                self.Put2( Ldw, self.rh, SP, item.a)   # item.r, item.a); 
                self.Put2( Ldw, self.rh, self.rh, 0); 
                item.r = self.rh; self.incR()
            elif item.mode == eClass.Const :
                if (item.a >= 0x10000) or (item.a < -0x10000) : mark( 'const too large') 
                self.Put1( Mov, self.rh, 0, item.a) 
                item.r = self.rh; self.incR()
            elif item.mode == eClass.RegI : self.Put2( Ldw, item.r, item.r, item.a)
            elif item.mode == eClass.Cond :
                self.Put3( 2, self.negated( item.r), 2);
                self.FixLink( item.b); self.self.Put1( Mov, self.rh, 0, 1); self.Put3(2, 7, 1);
                self.FixLink( item.a); self.self.Put1( Mov, self.rh, 0, 0); 
                item.r = self.rh; self.incR()        
            item.mode = eClass.Reg
    
    def loadAdr( self, item): 
        'emits load of the address of an item'
        if item.mode == eClass.Var :
            if item.r > 0 : # local
                self.Put1(Add, self.rh, SP, item.a); 
                item.r = self.rh 
            else:   # global
                self.Put1(Add, self.rh, BP, item.a) 
            self.incR()
        elif item.mode == eClass.Par: 
            self.Put2(Ldw, self.rh, SP, item.a); 
            self.Put1(Add, self.rh, self.rh, item.b); 
            item.r = self.rh; self.incR()
        elif (item.mode == eClass.RegI) & (item.a != 0) : 
            self.Put1(Add, item.r, item.r, item.a)
        else: mark( 'address error')         
        item.mode = eClass.Reg

    def loadCond( self, item): 
        'emits load of a boolean item'
        if item.type.form == eForm.Boolean :
            if item.mode == eClass.Const : 
                item.r = 15 - item.a * 8 
            else: 
                self.load( item); 
                self.Put1( Cmp, item.r, item.r, 0)
                item.r = NE; self.rh -= 1
            item.mode = eClass.Cond; item.a = 0; item.b = 0
        else: mark( 'not Boolean')

    def merged( self, L0, L1): # longints
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

    def MakeConstItem( self, item, type, value): 
        'make item a constant value'
        item.mode = eClass.Const
        item.type = type
        item.a = value

    def MakeItem( self, item, obj, curlev): 
        'make an item out of an object'
        item.mode = obj.class_; item.type = obj.type; item.a = obj.value; item.r = obj.level;
        if obj.class_ == eClass.Par : item.b = 0 
        if (obj.level > 0) & (obj.level != curlev) & (obj.class_ != eClass.Const) : mark( 'level error') 

    def Field( self, item, obj): # item:Item obj:Object
        'item = item.obj'
        if (item.mode == eClass.Var) or (item.mode == eClass.RegI) : 
          item.a = item.a + obj.value
        elif item.mode == Par : 
            self.Put2( Ldw, self.rh, item.r, item.a)
            item.mode = RegI; 
            item.r = self.rh; 
            item.a = obj.val; self.incR()

    def Index( self, xItem, yItem):
        'xItem = xItem[ yItem]'
        if yItem.mode == eClass.Const :
            if ( yItem.a < 0) or (yItem.a >= xItem.type.len) : mark("bad index") 
            if xItem.mode == eClass.Par : 
                self.Put2( Ldw, self.rh, item.r, item.a); 
                xItem.mode = RegI; 
                xItem.a = 0 
            xItem.a = xItem.a + yItem.a * xItem.type.base.size
        else: 
            size = xItem.type.base.size
            if yItem.mode != eClass.Reg : 
                self.load( yItem) 
                if size == 4 : self.Put1( Lsl, yItem.r, yItem.r, 2) 
                else: self.Put1( Mul, yItem.r, yItem.r, s) 
            if xItem.mode == Var :
                if xItem.r > 0 : self.Put0( Add, yItem.r, SP, yItem.r) 
                else: self.Put0( Add, yItem.r, BP, yItem.r) 
                xItem.mode = eClass.RegI; 
                xItem.r = yItem.r
            elif xItem.mode == eClass.Par :
                self.Put2( Ldw, self.rh, SP, xItem.a); 
                self.Put0( Add, yItem.r, self.rh, yItem.r); 
                xItem.mode = eClass.RegI; 
                xItem.r = yItem.r
            elif xItem.mode == eClass.RegI : 
                self.Put0( Add, xItem.r, xItem.r, yItem.r); 
                self.rh -= 1

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

    def And2( self, x, yItem): 
        ' x = x and yItem'
        if yItem.mode != Cond : self.loadCond(yItem) 
        x.a = merged(yItem.a, x.a); x.b = yItem.b; x.r = yItem.r
        return x

    def Or1( self, x): 
        'x = x or'
        if x.mode != Cond : self.loadCond(x) 
        self.Put3(BC, x.r, x.b);  x.b = pc-1; FixLink(x.a); x.a = 0
        return x

    def Or2( self, x, yItem):
        'x = x or yItem'
        if yItem.mode != Cond : self.loadCond(yItem) 
        x.a = yItem.a; 
        x.b = merged(yItem.b, x.b); 
        x.r = yItem.r
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

    def AddOp( self, op, x, yItem): 
        'x = x +/- yItem'
        if op == Lex.plus :
            if (x.mode == eClass.Const) & (yItem.mode == eClass.Const) : 
                x.a = x.a + yItem.a
            elif yItem.mode == eClass.Const : 
                self.load( x);
                if yItem.a != 0 : 
                    self.Put1( Add, x.r, x.r, yItem.a) 
            else: 
                self.load( x); self.load( yItem); 
                self.Put0( Add, self.rh-2, x.r, yItem.r)
                self.rh -= 1; x.r = self.rh-1
        else: # op = Lex.minus
            if (x.mode == eClass.Const) & (yItem.mode == eClass.Const) : 
                x.a = x.a - yItem.a
            elif yItem.mode == eClass.Const : 
                self.load( x);
                if yItem.a != 0 :
                   self.Put1( Sub, x.r, x.r, yItem.a) 
            else: 
                self.load( x); self.load( yItem)
                self.Put0( Sub, self.rh-2, x.r, yItem.r)
                self.rh -= 1; x.r = self.rh-1

    def MulOp( self, x, yItem): #Item);   
        'x = x * yItem'
        if (x.mode == eClass.Const) & (yItem.mode == eClass.Const) : 
            x.a = x.a * yItem.a
        elif (yItem.mode == eClass.Const) & (yItem.a == 2) : 
            self.load(x)
            self.Put1( Lsl, x.r, x.r, 1)
        elif yItem.mode == eClass.Const : 
            self.load(x)
            self.Put1( Mul, x.r, x.r, yItem.a)
        elif x.mode == eClass.Const : 
            self.load(yItem)
            self.Put1( Mul, yItem.r, yItem.r, x.a)
            x.mode = Reg; x.r = yItem.r
        else: 
            self.load( x); self.load( yItem); 
            self.Put0( Mul, self.rh-2, x.r, yItem.r)
            self.rh -= 1; x.r = self.rh-1

    def DivOp(self, op, x, yItem): #( LONGINT; VAR x, yItem: Item);   #  x = x op yItem *)
        if op == Lexdiv :
            if (x.mode == eClass.Const) & (yItem.mode == eClass.Const) :
              if yItem.a > 0 : x.a = x.a / yItem.a 
              else: Lex.mark( 'bad divisor') 
            elif (yItem.mode == eClass.Const) & (yItem.a == 2) : 
                self.load( x); 
                self.Put1( Asr, x.r, x.r, 1)
            elif yItem.mode == eClass.Const :
                if yItem.a > 0 : 
                    self.load( x)
                    self.Put1( Div, x.r, x.r, yItem.a) 
                else: Lex.mark( 'bad divisor') 
            else: 
                  self.load( yItem); self.load( x)
                  self.Put0( Div, self.rh-2, x.r, yItem.r)
                  self.rh -= 1; x.r = self.rh-1
        else:   # op = Lex.mod
            if (x.mode == Const) & (yItem.mode == Const) :
                if yItem.a > 0 : x.a = x.a % yItem.a 
                else: Lex.mark( 'bad modulus') 
            elif (yItem.mode == Const) & (yItem.a == 2) : 
                self.load( x)
                self.Put1( And, x.r, x.r, 1)
            elif yItem.mode == Const :
                if yItem.a > 0 : 
                      self.load( x); 
                      self.Put1( Div, x.r, x.r, yItem.a); 
                      self.Put0( Mov+U, x.r, 0, 0) 
                else: mark( 'bad modulus') 
            else: 
                self.load( yItem); self.load( x)
                self.Put0( Div, self.rh-2, x.r, yItem.r)
                self.Put0( Mov+U, self.rh-2, 0, 0)
                self.rh -= 1; x.r = self.rh-1

    def Relation( self, op, xItem, yItem): 
        'xItem = xItem ? yItem'
        if yItem.mode == eClass.Const : 
            self.load( xItem)
            self.Put1( Cmp, xItem.r, xItem.r, yItem.a)
            self.rh -= 1
        else: 
            self.load( xItem); self.load( yItem)
            self.Put0( Cmp, xItem.r, xItem.r, yItem.r)
            self.rh -= 2 
        self.setCC( xItem, self.relmap[op - Lex.eql])


    def Store( self, x, yItem):  #  x <= yItem 
        self.load( yItem);
        if x.mode == eClass.Var :
            if x.r > 0 : # local
                self.Put2( Stw, yItem.r, SP, x.a) 
            else: 
                self.Put2( Stw, yItem.r, BP, x.a) 
        elif x.mode == eClass.Par : 
            self.Put2( Ldw, self.rh, SP, x.a); 
            self.Put2( Stw, yItem.r, self.rh, x.b)
        elif x.mode == eClass.RegI : 
            self.Put2( Stw, yItem.r, x.r, x.a)
            self.rh -= 1
        else: mark( 'illegal assignment')
        self.rh -= 1
        

    def VarParam( self,  x, ftype): 
        xmd = x.mode; self.loadAdr(x);
        if ( ftype.form == eForm.Array) and (ftype.len < 0) : # open array
            if x.type.len >= 0 : 
                self.Put1( Mov, self.rh, 0, x.type.len) 
            else:  
                self.Put2( Ldw, self.rh, SP, x.a+4) 
            self.incR()
        elif ftype.form == eForm.Record :
            if xmd == Par : self.Put2( Ldw, self.rh, SP, x.a+4); self.incR() 

    def ValueParam( self, x): 
        return self.load( x)

    def OpenArrayParam( self, x):
        self.loadAdr( x);
        if x.type.len >= 0 : 
            self.Put1( Mov, self.rh, 0, x.type.len) 
        else: 
            self.Put2( Ldw, self.rh, SP, x.a+4) 
        self.incR()

  # ---------------------------------*)
  
    def CFJump( self, item): 
        'conditional forward jump'
        if item.mode != eClass.Cond : self.loadCond( item) 
        r = self.negated( item.r)
        self.Put3( 2, r, item.a); 
        self.fixLink( item.b); item.a = self.pc-1

    def FJump( self, L): # -> L
        'unconditional forward jump'
        self.Put3( 2, 7, L); 
        return self.pc-1

    def CBJump( self, item, L):
        'conditional backward jump'
        if item.mode != eClass.Cond : item = self.loadCond( item) 
        self.Put3( 2, self.negated( item.r), L- self.pc-1)
    
    def BJump( self, L): 
        'unconditional backward jump'
        self.Put3( 2, 7, L-self.pc-1)

    def Call( self, obj): # ( obj: Object)
        self.Put3( 3, 7, obj.value - self.pc-1); 
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

    def Ord( self, item): 
        self.load( item)

    def ReadInt( self, item): 
        self.loadAdr( item); 
        self.Put1( Mov, self.rh, 0, -4)
        self.Put2( Ldw, self.rh, self.rh, 0)
        self.Put2( Stw, self.rh, item.r, 0); 
        self.rh -= 1

    def eot( self, item): 
        self.Put1( Mov, self.rh, 0, -8); self.Put2(Ldw, self.rh, self.rh, 0)
        self.setCC( item, EQ)

    def WriteInt( self, item): 
        self.load( item); 
        self.Put1( Mov, self.rh, 0, -4)
        self.Put2( Stw, item.r, self.rh, 0)
        self.rh -= 1
        return item

    def WriteChar( self, item): 
        self.load( item); 
        self.Put1( Mov, self.rh, 0, -8)
        self.Put2( Stw, item.r, self.rh, 0)
        self.rh -= 1
        return item

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
        if r < 13 :    print 'R%d' % r,
        elif r == 13 : print 'BP',
        elif r == 14 : print 'SP',
        elif r == 15 : print 'LNK',
  
    # pq
    # 00uv |  a(4) | b(4) | opcode(4) |  xxxx  | c(4) |  # a = opcode( b, c)
    # 01uv |  a(4) | b(4) | opcode(4) |     imm(16)   |  # a = opcode( b, imm)
    # 10uv |  a(4) | b(4) |                 off(20)   |  # load / store
    # 11uv |cond(4)|         imm(24)                  |  # a = br(cond, imm)

    def Decode( self):
        print 'Decode:'
        i = 0;
        while i < self.pc:
            w = self.code[ i]
            a = w / 0x1000000 % 0x10
            b = w / 0x100000 % 0x10
            print '%04X \t' % i,
            if (w & 0x80000000)  == 0 :  # ~p:  register instruction
                op = w / 0x10000 % 0x10
                print self.mnemo0[ op],  
                print '\t',
                self.WriteReg( a)
                if op != Mov : self.WriteReg( b)
                if (w & 0x40000000) == 0 : # ~q 
                    self.WriteReg( w % 0x10) 
                else: 
                    c = w % 0x10000
                    if (w & 0x10000000) != 0: # v sign extends
                        c = c - 0x10000 
                    print hex( c)
            elif (w & 0x40000000) == 0 :  # load/store
                if (w & 0x20000000) != 0 :  print 'STW', 
                else: print 'LDW',
                print '\t',
                self.WriteReg( a)
                self.WriteReg( b) 
                print '[%x]' %  (w % 0x100000)

            else:        # Branch instr
                mnem = 'B'
                if ( w & 0x10000000) != 0 : mnem += 'L'
                if a == 7:   mnem += ' '       # (always True)
                else: mnem += self.mnemo1[ a]   # conditional
                print mnem +'\t\t',
                if ( w & 0x20000000) == 0: # u 
                    self.WriteReg( w % 0x10) 
                    print
                else:
                    w  %= 0x100000
                    if w & 0x80000 : w = w - 0x100000 
                    if w >= 0 : print '+',
                    print hex( w)      
            i += 1
        print


    def Execute( self, debug=None):
        mcu = Risc()
        mcu.run( self.code, self.pc, debug)

