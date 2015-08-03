#!/usr/bin/env python
'''
  MODULE OSP; (* NW 23.9.93 / 20.10.07 / 30.10.2013 *)
'''
# import pdb
import risc
import osg
from osg import Osg, eClass, eForm
from oss import Lex, Lexer, mark, errcnt

level = 0

# expression1: def (VAR x: osg.Item);  # to avoid forward reference

def NewObj( ident, cl): # -> objDesc
    scope = universe[ topScope]
    for ident in scope.idents:
        if ident.name == ident : 
            Lex.mark( 'multiple definitions')
            return item
    new = osg.ObjDesc( ident, cl)
    scope.idents.append( new) 
    return new

def find( ident): # -> obj
    'search identifier in curren scope and above'
    for scope in universe[ topScope:] :
        for x in scope.idents:
            if x.name == ident: return x 
    else:  
        mark( 'undefined'); return dummy 

def FindField( ident, lst):
    for x in lst: 
        if x.name == ident : return x
    else: 
        Lex.mark( 'undefined'); return dummy 

def Check( sym, s, msg): # -> sym
    if sym == s : sym = lex.get(); return sym 
    else: mark( msg) 

def CheckInt( x): # osg.Item
    if x.type.form != osg.Integer : mark('not integer') 

def CheckBool( x): # osg.Item
    if x.type.form != osg.Boolean : mark('not Boolean') 

def OpenScope( name):
    scope = osg.ObjScope( name=name, idents=[])
    universe.insert( topScope, scope) 
     
def CloseScope():
    universe.pop( topScope)

# -------------------- Parser ---------------------

def selector( sym, x): # osg.Item
    while ( sym == Lex.lbrak) or ( sym == Lex.period) :
        if sym == Lex.lbrak :
            sym = lex.get(); y = expression1()
            if x.type.form == osg.Array :
                CheckInt( y); osg.Index( x, y); x.type = x.type.base
            else: mark('not an array')          
            sym = Check( sym, Lex.rbrak, 'no ]')
        else: # period 
            sym, id_ = lex.get()
            if sym == Lex.ident :
                if x.type.form == osg.Record :
                    obj = FindField( id_, x.type.fieldList)
                    sym = lex.get()
                    osg.Field( x, obj) 
                    x.type = obj.type 
                else: mark('not a record')
            else: mark( 'ident?')      
    return sym

def CompTypes( t0, t1): # (osg.Type): # -> BOOLEAN;
    'Compatible Types'
    return (t0 == t1) or \
           (t0.form == osg.Array) and (t1.form == osg.Array) and CompTypes( t0.base, t1.base)


def Parameter( sym, par): # osg.Object
    sym = expression( sym, x)
    if par :
        varpar = par.class_ == osg.Par
        if CompTypes( par.type, x.type) :
            if not varpar : osg.ValueParam( x)
            else: osg.VarParam( x, par.type)
        elif ( x.type.form == osg.Array) and (par.type.form == osg.Array) and \
        ( x.type.base.form == par.type.base.form) and (par.type.len < 0) :
            osg.OpenArrayParam( x)
    else: mark('incompatible parameters')
    return sym
  
def ParamList( sym, obj): # osg.Object
    par = obj.dsc; n = 0;
    if sym != Lex.rparen :
        Parameter(par); n = 1;
        while sym <= Lex.comma :
            sym = Check( sym, Lex.Comma, 'comma?')
            if par : par = par.next 
            INC(n); Parameter(par)        
        sym = Check( sym, Lex.rparen, ') missing')
    else: sym = lex.get();
    if n < obj.nofpar : mark('too few params')
    elif n > obj.nofpar : mark('too many params')
    return sym

def StandFunc( sym, x, fctno): 
    'parse a builtin function'
    if sym == Lex.lparen :
        sym = lex.get();
        if fctno == 0 :     # ORD
            sym = expression1( sym, x); 
            osg.Ord( x)
            x.type = gen.intType
        elif fctno == 1 : # eot 
            osg.eot( x)      
        if sym == Lex.rparen : sym = lex.get() 
        else: mark( 'rparen expected') 
    else: mark( 'param missing'); osg.MakeConstItem( x, osg.intType, 0)
    return sym

def factor( sym, x): # -> sym
    # sync
    if (sym < Lex.char_) or (sym > Lex.ident) : 
        mark('expression expected')
        while True:
           sym = lex.get() 
           if (sym >= Lex.int) and (sym <= Lex.ident): break
    if sym == Lex.ident :
        obj = find( lex.value); sym = lex.get();
        if obj.class_ == osg.SFunc :
            if not obj.type : mark('not a function'); obj.type = osg.intType 
            StandFunc( x, obj.val); x.type = obj.type
        else: gen.MakeItem( x, obj, level); sym = selector( sym, x)
    elif sym == Lex.int_ : gen.MakeConstItem( x, intType, lex.value); sym = lex.get()
    elif sym == Lex.char_ : gen.MakeConstItem( x, intType, lex.value); sym = lex.get()
    elif sym == Lex.lparen :
        sym = lex.get();
        if sym != Lex.rparen : sym = expression1( sym, x) 
        Check(Lex.rparen, 'no )')
    elif sym == Lex.not_ : sym = lex.get(); sym = factor( sym, x); CheckBool(x); osg.Not(x)
    elif sym == Lex.false_ : sym = lex.get(); gen.MakeConstItem( x, boolType, 0)
    elif sym == Lex.true_ : sym = lex.get(); gen.MakeConstItem( x, boolType, 1)
    else: mark( 'factor?'); gen.MakeItem( x, dummy, level)
    return sym

def term( sym, x): # -> sym 
    y = osg.Item()
    sym = factor( sym, x)
    while (sym >= Lex.times) and (sym <= Lex.and_) :
        op = sym; sym = lex.get();
        if op == Lex.times : 
            CheckInt( x); sym = factor( sym, y); CheckInt( y); osg.MulOp( x, y)
        elif ( op == Lex.div) or ( op == Lex.mod) : 
            CheckInt( x); sym = factor( sym, y); CheckInt( y); osg.DivOp( op, x, y)
        else: # op == and_
            CheckBool( x); osg.And1( x); sym = factor( sym, y); CheckBool( y); osg.And2( x, y)
    return sym

def SimpleExpression( sym, x): # sym
    if sym == Lex.plus : sym = lex.get(); sym = term( sym); CheckInt(x)
    elif sym == Lex.minus : sym = lex.get(); sym, x = term( sym); CheckInt( x); osg.Neg( x)
    else: sym = term( sym, x)
    while (sym >= Lex.plus) and (sym <= Lex.or_) :
        op = sym; sym = lex.get();
        if op == Lex.or_ : osg.Or1(x); CheckBool(x); sym, y = term( sym); CheckBool( y); osg.Or2( x, y)
        else: CheckInt(x); sym, y = term( sym); CheckInt(y); osg.AddOp(op, x, y)
    return sym

def expression( sym, x): # -> sym
    sym = SimpleExpression( sym, x)
    if (sym >= Lex.eql) and (sym <= Lex.geq) :
        op = sym; sym = lex.get(); sym = SimpleExpression( sym, y)
        if x.type == y.type : osg.Relation( op, x, y) 
        else: mark( 'incompatible types') 
        x.type = osg.boolType
    return sym

def StandProc( sym, pno): 
    if sym == Lex.lparen :
        sym = lex.get(); expression(x);
        if pno == 0 :  osg.ReadInt(x)
        elif pno == 1 : osg.WriteInt(x)
        elif pno == 2 : osg.WriteChar(x)
        elif pno == 3 : osg.WriteLn
    else: 
        mark('no lparen')          
    if sym == Lex.rparen : sym = lex.get() 
    else: mark( 'no rparen') 
    return sym

def StatSequence( sym):
    global level
    x = osg.Item()
    y = osg.Item()
    while True: # sync 
        if not ( (sym == Lex.ident) or ( sym >= Lex.if_) and ( sym <= Lex.repeat) or ( sym >= Lex.semicolon)) :
            mark( 'statement expected');
            while True: 
                sym = lex.get() 
                if ( sym == Lex.ident) or ( sym >= Lex.if_): break  

        if sym == Lex.ident :
            obj = find( lex.value); sym = lex.get()
            if obj.class_ == osg.eClass.SProc : StandProc( obj.val)
            else: gen.MakeItem( x, obj, level); sym = selector( sym, x);
            if sym == Lex.becomes :                     # assignment
                sym = lex.get(); sym = expression( sym, y); 
                if ( x.type.form in [ eForm.Boolean, eForm.Integer]) and ( x.type.form == y.type.form) : gen.Store( x, y)
                else: mark( 'incompatible assignment')
            elif sym == Lex.eql : mark( 'should be =='); sym = lex.get(); sym = expression( sym, y)
            elif sym == Lex.lparen : # procedure call
                sym = lex.get();
                if (obj.class_ == osg.Proc) and (obj.type == NIL) : sym = ParamList( obj); osg.Call(obj);
                else: mark('not a procedure')
            elif obj.class_ == osg.Proc :               # procedure call without parameters
                if obj.nofpar > 0 : mark( 'missing parameters') 
                if not obj.type : osg.Call(obj) 
                else: mark( 'not a procedure') 
            elif (obj.class_ == osg.SProc) and (obj.val == 3) : osg.WriteLn()
            elif obj.class_ == osg.Typ : mark('illegal assignment')
            else: mark('not a procedure')

        elif sym == Lex.if_ :
            sym = lex.get(); expression(x); CheckBool(x); osg.CFJump(x); Check(Lex.then, 'no :')
            StatSequence; L = 0;
            while sym == Lex.elsif :
                sym = lex.get(); osg.FJump(L); osg.FixLink(x.a); expression(x); CheckBool(x); osg.CFJump(x);
                if sym == Lex.then : sym = lex.get() 
                else: mark(':?') 
                StatSequence
            if sym == Lex.else_ :
                sym = lex.get(); osg.FJump(L); osg.FixLink(x.a); StatSequence
            else: osg.FixLink(x.a)    
            osg.FixLink(L);
            if sym == Lex.end : sym = lex.get() 
            else: mark('END?') 

        elif sym == Lex.while_ :
            sym = lex.get(); L = osg.pc; expression(x); CheckBool(x); osg.CFJump(x);
            Check(Lex.do, 'no :'); StatSequence; osg.BJump(L); osg.FixLink(x.a);
            Check(Lex.end, 'no END')

        elif sym == Lex.repeat :
            sym = lex.get(); L = osg.pc; StatSequence;
            if sym == Lex.until :
                sym = lex.get(); expression(x); CheckBool(x); osg.CBJump(x, L)
            else: mark('missing UNTIL'); sym = lex.get()  
        gen.CheckRegs()
        if sym == Lex.semicolon : sym = lex.get()
        elif sym < Lex.semicolon : mark( 'missing semicolon?')
        if sym > Lex.semicolon: break
    return sym

def IdentList( sym, cl): # -> identsList
    'appends new identifiers to current scope with given class, returns them in a list'
    if sym == Lex.ident :
        identsList = [ NewObj( lex.value, cl)]
        sym = lex.get();
        while sym == Lex.comma :
            sym = lex.get();
            if sym == Lex.ident : 
                identsList.append( NewObj( lex.value, cl))
                sym = lex.get()
            else: mark('ident?')
        sym = Check( sym, Lex.colon, 'no :')
    return sym, identsList

def Type( sym, type):
    type = intType;         #sync
    if ( sym != Lex.ident) and ( sym < Lex.array) : 
        mark( 'type?');
        while True: 
            sym = lex.get() 
            if ( sym == Lex.ident) or ( sym >= Lex.array) : break
    if sym == Lex.ident :
        obj = find( lex.value); sym = lex.get();
        if obj.class_ == eClass.Typ : type = obj.type 
        else: mark( 'type?') 
    elif sym == Lex.array :
        sym = lex.get(); sym = expression( sym, x);
        if ( x.mode != osg.Const) or ( x.a < 0) : mark('bad index') 
        if sym == Lex.of : sym = lex.get() 
        else: mark('OF?') 
        sym = Type( sym, tp); 
        type = TypeDesc( form = osg.Array); type.base = tp;
        type.len = x.a; type.size = type.len * tp.size
    elif sym == Lex.record :
        sym = lex.get(); NEW(type); type.form = osg.Record; type.size = 0; OpenScope;
        while True:
            if sym == Lex.ident :
                IdentList(osg.Fld, first); Type(tp); obj = first;
                while obj != NIL :
                    obj.type = tp; 
                    obj.val = type.size; 
                    type.size = type.size + obj.type.size; 
                    obj = obj.next                  
            if sym == Lex.semicolon : sym = lex.get()
            elif sym == Lex.ident : mark('; ?')
            if sym != oss.ident: break
        type.dsc = topScope.next; 
        CloseScope; 
        Check(Lex.end, 'no END')
    else: mark('ident?')  
    return sym

def Declarations( sym, varsize): # -> sym
    # sync
    x = osg.Item()
    tp = osg.TypeDesc()
    if (sym < Lex.const) and (sym != Lex.end) :
        mark('declaration?');
        while True: 
            sym = lex.get() 
            if (sym >= Lex.const) or (sym == Lex.end): break
    if sym == Lex.const :
        sym = lex.get();
        while sym == Lex.ident :
            obj = NewObj( osg.eClass.Const); sym = lex.get()
            if sym == Lex.eql : sym = lex.get() 
            else: mark('=?') 
            sym = expression( sym, x)
            if x.mode == osg.eClass.Const : obj.val = x.a; obj.type = x.type
            else: mark( 'expression not constant')      
            sym = Check( sym, Lex.semicolon, '; expected')
    if sym == Lex.type :
        sym = lex.get();
        while sym == Lex.ident :
            obj = NewObj( eClass.Typ); 
            sym = lex.get()
            if sym == Lex.eql : sym = lex.get() 
            else: mark('=?')  
            sym = Type( obj.type)
            sym = Check( sym, Lex.semicolon, '; expected')
    if sym == Lex.var :
        sym = lex.get();
        while sym == Lex.ident :
            sym, iList = IdentList( sym, eClass.Var)
            sym = Type( sym, tp);
            for obj in iList:
                obj.type = tp
                obj.lev = level
                obj.value = varsize         # address
                varsize += obj.type.size
            sym = Check( sym, Lex.semicolon, '; expected')
    if ( sym >= Lex.const) and ( sym <= Lex.var) : 
        mark('declaration in bad order') 
    return sym

def FPSection( sym, adr, nofpar):
    if sym == Lex.var : sym = lex.get(); IdentList(osg.Par, first)
    else: IdentList(osg.Var, first)
    if sym == Lex.ident :
        find(obj); sym = lex.get();
        if obj.class_ == osg.Typ : tp = obj.type 
        else: mark('type?'); tp = osg.intType 
    else: mark('ident?'); tp = osg.intType
    if first.class_ == osg.Var :
        parsize = tp.size;
        if tp.form >= osg.Array : mark('no struct params') 
    else: parsize = WordSize
    obj = first;
    while obj != NIL :
        INC(nofpar); obj.type = tp; obj.lev = level; obj.val = adr; adr = adr + parsize;
        obj = obj.next 
    return sym

def ProcedureDecl( sym):
    marksize = 4;
    # ProcedureDecl  
    sym = lex.get();
    if sym == Lex.ident :
        procid = Lex.id;
        NewObj( proc, osg.Proc); sym = lex.get(); parblksize = marksize; nofpar = 0;
        OpenScope;  
        level += 1; 
        proc.val = -1;
        if sym == Lex.lparen :
            sym = lex.get();
            if sym == Lex.rparen : sym = lex.get()
            else: 
                sym = FPSection( sym, parblksize, nofpar);
                while sym == Lex.semicolon : sym = lex.get(); sym = FPSection( sym, parblksize, nofpar) 
                if sym == Lex.rparen : sym = lex.get() 
                else: mark(')?')
        locblksize = parblksize; proc.type = NIL; proc.dsc = topScope.next; proc.nofpar = nofpar;
        sym = Check( sym, Lex.semicolon, '; expected');
        sym = Declarations( sym, locblksize); proc.dsc = topScope.next;
        while sym == Lex.procedure :
            sym = ProcedureDecl( sym); sym = Check( sym, Lex.semicolon, '; expected')   
        proc.val = osg.pc; osg.Enter(parblksize, locblksize);
        if sym == Lex.begin : sym = lex.get(); StatSequence 
        sym = Check( sym, Lex.end, 'no END')
        if sym == Lex.ident :
            if procid != Lex.id : mark('no match') 
            sym = lex.get()   
        osg.Return(locblksize)
        level -= 1; 
        CloseScope()
    return sym

def Module( sym):
    if sym == Lex.module_ :
        sym = lex.get();
        if sym == Lex.times : 
            tag = 1
            sym = lex.get() 
        else: tag = 0 
        gen.Open()
        OpenScope('module')
        dc = 0
        level = 0
        if sym == Lex.ident :
            modid = lex.value; 
            sym = lex.get()
            print 'Compiling module:', modid
        else: mark('ident?')
        sym = Check( sym, Lex.semicolon, '; expected')
        sym = Declarations( sym, dc)
        while sym == Lex.procedure : sym = ProcedureDecl( sym); sym = Check( sym, Lex.semicolon, '; expected') 
        gen.Header(dc);
        if sym == Lex.begin : sym = lex.get(); sym = StatSequence( sym) 
        sym = Check( sym, Lex.end, 'no END');
        if sym == Lex.ident :
            if modid != lex.value : Lex.mark( 'no match') 
            sym = lex.get()
        else: mark( 'ident?')      
        if sym != Lex.period : mark('. ?') 
        CloseScope();
        if  errcnt == 0 :
            gen.Close() 
            print 'Code generated:', gen.pc, dc
        else: mark('MODULE?')

def Compile():
    # Oberon.GetSelection(T, beg, end, time);
    # if time >= 0 : Lex.Init(T, beg); 
    sym = lex.get()
    Module( sym) 

def addBuiltin( name, cl, value, type):
    obj = NewObj( '', cl)
    obj.name = name
    obj.value = value
    obj.type = type

def universeView():
    for scope in universe:
        print scope.name
        for i, ident in enumerate( scope.idents):
            print '<',i,'>', ident
        


print 'Oberon-0 Compiler OSP  30.10.2013'
print
lex = Lexer( iter( 'MODULE Test;\r\n VAR a : INTEGER; BEGIN a := 1 \r\nEND Test.\r\n'))
gen = Osg()
boolType = osg.TypeDesc( 'Bool', form = eForm.Boolean, size = 4)
intType  = osg.TypeDesc( 'Integer', form = eForm.Integer, size = 4)
dummy    = osg.ObjDesc( 'dummy', osg.eClass.Var); dummy.type = intType

universe = []; topScope = 0 
level = 0
OpenScope( 'root')
# expression1 = expression
addBuiltin( 'eot', osg.eClass.SFunc, 1, boolType)
addBuiltin( 'ReadInt', osg.eClass.SProc, 0, None)
addBuiltin( 'WriteInt', osg.eClass.SProc, 1, None)
addBuiltin( 'WriteChar', osg.eClass.SProc, 2, None)
addBuiltin( 'WriteLn', osg.eClass.SProc, 3, None)
addBuiltin( 'ORD', osg.eClass.SFunc, 0, intType)
addBuiltin( 'BOOLEAN', osg.eClass.Typ, 0, boolType)
addBuiltin( 'INTEGER', osg.eClass.Typ, 1, intType)
Compile()

    # universeView() # dbg
