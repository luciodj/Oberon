#!/usr/bin/env python
'''
  MODULE OSP; (* NW 23.9.93 / 20.10.07 / 30.10.2013 *)
'''
# import pdb
import risc
import osg
from osg import Osg, eClass, eForm
from oss import Lex, Lexer, mark, getErrcnt

level = 0

def NewObj( name, cl): # -> objDesc
    scope = universe[ topScope]
    for ident in scope.idents:
        if ident.name == name : 
            mark( 'multiple definitions')
            return ident
    new = osg.ObjDesc( name, cl)
    scope.idents.append( new) 
    return new

def find( ident): # -> obj
    'search identifier in curren scope and above'
    for scope in universe[ topScope:] :
        for i in scope.idents:
            if i.name == ident: return i 
    else:  
        mark( 'undefined'); return dummy 

def FindField( ident, lst):
    for i in lst: 
        if i.name == ident : return i
    else: 
        Lex.mark( 'undefined'); return dummy 

def Check( sym, s, msg): # -> sym
    if sym == s : sym = lex.get(); return sym 
    else: mark( msg) 

def CheckInt( item): 
    if item.type.form != eForm.Integer : mark( 'not integer') 

def CheckBool( item): 
    if item.type.form != eForm.Boolean : mark( 'not Boolean') 

def OpenScope( name):
    scope = osg.ObjScope( name=name, idents=[])
    universe.insert( topScope, scope) 
     
def CloseScope():
    universe.pop( topScope)

# -------------------- Parser ---------------------

def selector( sym, xItem): # osg.Item
    yItem = osg.Item()
    while ( sym == Lex.lbrak) or ( sym == Lex.period) :
        if sym == Lex.lbrak :
            sym = lex.get(); sym = expression( sym, yItem)
            if xItem.type.form == eForm.Array :
                CheckInt( yItem); gen.Index( xItem, yItem); xItem.type = xItem.type.base
            else: mark('not an array')          
            sym = Check( sym, Lex.rbrak, 'no ]')
        else: # period 
            sym, id_ = lex.get()
            if sym == Lex.ident :
                if xItem.type.form == osg.Record :
                    obj = FindField( id_, xItem.type.fieldList)
                    sym = lex.get()
                    osg.Field( xItem, obj) 
                    xItem.type = obj.type 
                else: mark('not a record')
            else: mark( 'ident?')      
    return sym

def CompTypes( t0, t1): # (osg.Type): # -> BOOLEAN;
    'Compatible Types'
    return (t0 == t1) or \
           (t0.form == osg.Array) and (t1.form == osg.Array) and CompTypes( t0.base, t1.base)


def Parameter( sym, par): # osg.Object
    xItem = Item()
    sym = expression( sym, xItem)
    if par :
        varpar = par.class_ == eClass.Par
        if CompTypes( par.type, xItem.type) :
            if not varpar : osg.ValueParam( xItem)
            else: osg.VarParam( xItem, par.type)
        elif ( xItem.type.form == osg.Array) and (par.type.form == osg.Array) and \
        ( xItem.type.base.form == par.type.base.form) and (par.type.len < 0) :
            osg.OpenArrayParam( xItem)
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

def StandFunc( sym, xItem, fctno): 
    'parse a builtin function'
    if sym == Lex.lparen :
        sym = lex.get();
        if fctno == 0 :     # ORD
            sym = expression( sym, xItem); 
            gen.Ord( xItem); xItem.type = intType
            xItem.type = intType
        elif fctno == 1 : # eot 
            osg.eot( xItem)      
        if sym == Lex.rparen : sym = lex.get() 
        else: mark( 'rparen expected') 
    else: mark( 'param missing'); osg.MakeConstItem( xItem, intType, 0)
    return sym

def factor( sym, xItem): # -> sym
    # sync
    if (sym < Lex.char_) or (sym > Lex.ident) : 
        mark('expression expected')
        while True:
           sym = lex.get() 
           if (sym >= Lex.int_) and (sym <= Lex.ident): break
    if sym == Lex.ident :
        obj = find( lex.value); sym = lex.get();
        if obj.class_ == eClass.SFunc :
            if not obj.type : mark('not a function'); obj.type = intType 
            sym = StandFunc( sym, xItem, obj.value); xItem.type = obj.type
        else: gen.MakeItem( xItem, obj, level); sym = selector( sym, xItem)
    elif sym == Lex.int_ : gen.MakeConstItem( xItem, intType, lex.value); sym = lex.get()
    elif sym == Lex.char_ : gen.MakeConstItem( xItem, intType, lex.value); sym = lex.get()
    elif sym == Lex.lparen :
        sym = lex.get();
        if sym != Lex.rparen : sym = expression1( sym, xItem) 
        Check(Lex.rparen, 'no )')
    elif sym == Lex.not_ : sym = lex.get(); sym = factor( sym, xItem); CheckBool(xItem); osg.Not(xItem)
    elif sym == Lex.false_ : gen.MakeConstItem( xItem, boolType, 0); sym = lex.get()
    elif sym == Lex.true_ :  gen.MakeConstItem( xItem, boolType, 1); sym = lex.get()
    else: mark( 'factor?'); gen.MakeItem( xItem, dummy, level)
    return sym

def term( sym, xItem): # -> sym 
    yItem = osg.Item()
    sym = factor( sym, xItem)
    while (sym >= Lex.times) and (sym <= Lex.and_) :
        op = sym; sym = lex.get();
        if op == Lex.times : 
            CheckInt( xItem); sym = factor( sym, yItem); CheckInt( yItem); osg.MulOp( xItem, yItem)
        elif ( op == Lex.div) or ( op == Lex.mod) : 
            CheckInt( xItem); sym = factor( sym, yItem); CheckInt( yItem); osg.DivOp( op, xItem, yItem)
        else: # op == and_
            CheckBool( xItem); osg.And1( xItem); sym = factor( sym, yItem); CheckBool( yItem); osg.And2( xItem, yItem)
    return sym

def SimpleExpression( sym, xItem): # sym
    yItem = osg.Item()
    if sym == Lex.plus : sym = lex.get(); sym = term( sym, xItem); CheckInt( xItem)
    elif sym == Lex.minus : sym = lex.get(); sym = term( sym, xItem); CheckInt( xItem); osg.Neg( xItem)
    else: 
        sym = term( sym, xItem); 
    # import pdb; pdb.set_trace()
    while ( sym >= Lex.plus) and ( sym <= Lex.or_) :
        op = sym; sym = lex.get();
        if op == Lex.or_ : 
            gen.Or1( xItem); CheckBool( xItem)
            sym = term( sym, yItem); CheckBool( yItem)
            gen.Or2( xItem, yItem)
        else: 
            CheckInt( xItem)
            sym = term( sym, yItem); CheckInt( yItem)
            gen.AddOp(op, xItem, yItem)
    return sym

def expression( sym, xItem): # -> sym
    yItem = osg.Item()
    sym = SimpleExpression( sym, xItem)
    if (sym >= Lex.eql) and (sym <= Lex.geq) :
        op = sym; sym = lex.get(); sym = SimpleExpression( sym, yItem)
        if xItem.type == yItem.type : gen.Relation( op, xItem, yItem) 
        else: mark( 'incompatible types') 
        xItem.type = boolType
    return sym

def StandProc( sym, pno): 
    if sym == Lex.lparen :
        xItem = osg.Item()
        sym = lex.get(); sym = expression( sym, xItem)
        if pno == 0 :  gem.ReadInt( xItem)
        elif pno == 1 : gen.WriteInt( xItem)
        elif pno == 2 : gen.WriteChar( xItem)
        elif pno == 3 : gen.WriteLn()
    else: 
        mark('no lparen')          
    if sym == Lex.rparen : sym = lex.get() 
    else: mark( 'no rparen') 
    return sym

def StatSequence( sym):
    global level
    xItem = osg.Item()
    yItem = osg.Item()
    while True: 
        if not ( (sym == Lex.ident) or ( sym >= Lex.if_) and ( sym <= Lex.repeat) or ( sym >= Lex.semicolon)) :
            mark( 'statement expected');
            while True: 
                sym = lex.get() 
                if ( sym == Lex.ident) or ( sym >= Lex.if_): break  

        if sym == Lex.ident :
            obj = find( lex.value); sym = lex.get()
            if obj.class_ == eClass.SProc : sym = StandProc( sym, obj.value)
            else: 
                gen.MakeItem( xItem, obj, level); sym = selector( sym, xItem);
                if sym == Lex.becomes :                     # assignment
                    sym = lex.get(); sym = expression( sym, yItem); 
                    if ( xItem.type.form in [ eForm.Boolean, eForm.Integer]) and ( xItem.type.form == yItem.type.form) : gen.Store( xItem, yItem)
                    else: mark( 'incompatible assignment')
                elif sym == Lex.eql : mark( 'should be =='); sym = lex.get(); sym = expression( sym, yItem)
                elif sym == Lex.lparen : # procedure call
                    sym = lex.get();
                    if (obj.class_ == gen.Proc) and (obj.type == NIL) : sym = ParamList( obj); gen.Call(obj);
                    else: mark('not a procedure')
                elif obj.class_ == eClass.Proc :               # procedure call without parameters
                    if obj.nofpar > 0 : mark( 'missing parameters') 
                    if not obj.type : gen.Call(obj) 
                    else: mark( 'not a procedure') 
                elif (obj.class_ == eClass.SProc) and ( obj.value == 3) : gen.WriteLn()
                elif obj.class_ == eClass.Typ : mark( 'illegal assignment')
                else: mark( 'not a procedure')

        elif sym == Lex.if_ :
            sym = lex.get(); sym = expression( sym, xItem); CheckBool( xItem)
            gen.CFJump( xItem)
            sym = Check( sym, Lex.then, 'no :')
            sym = StatSequence( sym); L = 0
            while sym == Lex.elsif :
                sym = lex.get(); L = gen.FJump( L); gen.fixLink( xItem.a)
                sym = expression( sym, xItem); CheckBool( xItem); 
                gen.CFJump( xItem);
                if sym == Lex.then : sym = lex.get() 
                else: mark(':?') 
                StatSequence
            if sym == Lex.else_ :
                sym = lex.get(); L = gen.FJump( L); gen.fixLink(xItem.a); StatSequence
            else: gen.fixLink(xItem.a)    
            gen.fixLink(L);
            if sym == Lex.end : sym = lex.get() 
            else: mark('END ?') 

        elif sym == Lex.while_ :
            sym = lex.get(); L = osg.pc; sym = expression( sym, xItem); CheckBool(xItem); gen.CFJump(xItem);
            Check(Lex.do, 'no :'); StatSequence; gen.BJump(L); gen.fixLink(xItem.a);
            Check(Lex.end, 'no END')

        elif sym == Lex.repeat :
            sym = lex.get(); L = osg.pc; sym = StatSequence( sym);
            if sym == Lex.until :
                sym = lex.get(); sym = expression( sym, xItem); sym = CheckBool( sym, xItem); gen.CBJump(xItem, L)
            else: mark('missing UNTIL'); sym = lex.get()  
        gen.checkRegs()
        if sym == Lex.semicolon : sym = lex.get()
        elif sym < Lex.semicolon : mark( 'missing semicolon?')
        if sym > Lex.semicolon: break
    return sym

def identList( sym, idList, cl): 
    'appends new identifiers to current scope with given class, returns them in a list'
    while sym == Lex.ident :
        idList.append( NewObj( lex.value, cl))
        sym = lex.get();
        if sym == Lex.colon : break
        elif sym == Lex.comma : sym = lex.get()
        else: mark( 'no ,')
    if sym != Lex.colon : mark('no :')
    sym = lex.get()
    return sym

def Type( sym): #  -> sym, type
    if ( sym != Lex.ident) and ( sym < Lex.array) : 
        mark( 'type?');
        while True: 
            sym = lex.get() 
            if ( sym == Lex.ident) or ( sym >= Lex.array) : break
    if sym == Lex.ident :
        obj = find( lex.value); sym = lex.get()
        if obj.class_ == eClass.Typ : type = obj.type
        else: mark( 'type?') 
    elif sym == Lex.array :
        xItem = osg.Item()
        sym = lex.get(); sym = expression( sym, xItem);
        if ( xItem.mode != eClass.Const) or ( xItem.a < 0) : mark('bad index') 
        if sym == Lex.of : sym = lex.get() 
        else: mark('OF?')
        sym, tp = Type( sym); 
        type = osg.TypeDesc( form = eForm.Array); type.base = tp;
        type.len = xItem.a; type.size = type.len * tp.size
    elif sym == Lex.record :
        sym = lex.get() 
        type = osg.TypeDesc( form = eForm.Record, size = 0); 
        OpenScope( 'record')
        while True:
            if sym == Lex.ident :
                iList = []
                sym, iList = identList( sym, iList, eForm.Fld ); 
                sym = Type( sym, tp) 
                while obj != NIL :
                    obj.type = tp; 
                    obj.value = type.size; 
                    type.size = type.size + obj.type.size; 
                    obj = obj.next                  
            if sym == Lex.semicolon : sym = lex.get()
            elif sym == Lex.ident : mark('; ?')
            if sym != oss.ident: break
        type.dsc = topScope.next; 
        CloseScope; 
        Check( Lex.end, 'no END')
    else: mark('ident?')  
    return sym, type

def Declarations( sym, varsize): # -> sym, varsize
    # sync
    xItem = osg.Item()
    if (sym < Lex.const) and (sym != Lex.end) :
        mark('declaration?');
        while True: 
            sym = lex.get() 
            if (sym >= Lex.const) or (sym == Lex.end): break
    if sym == Lex.const :
        sym = lex.get();
        while sym == Lex.ident :
            obj = NewObj( lex.value, eClass.Const); sym = lex.get()
            if sym == Lex.eql : sym = lex.get() 
            else: mark('=?') 
            sym = expression( sym, xItem)
            if xItem.mode == eClass.Const : obj.value = xItem.a; obj.type = xItem.type
            else: mark( 'expression not constant')      
            sym = Check( sym, Lex.semicolon, '; expected')
    if sym == Lex.type :
        sym = lex.get();
        while sym == Lex.ident :
            obj = NewObj( lex.value, eClass.Typ); 
            sym = lex.get()
            if sym == Lex.eql : sym = lex.get() 
            else: mark('=?')  
            sym, obj.type = Type( sym)
            sym = Check( sym, Lex.semicolon, '; expected')
    if sym == Lex.var :
        sym = lex.get()
        iList = []
        sym = identList( sym, iList, eClass.Var)
        sym, tp = Type( sym)
        for obj in iList:
            obj.type = tp
            obj.lev = level
            obj.value = varsize         # address
            varsize += obj.type.size
        sym = Check( sym, Lex.semicolon, '; expected')
    if ( sym >= Lex.const) and ( sym <= Lex.var) : 
        mark('declaration in bad order') 
    return sym, varsize

def FPSection( sym, adr, nofpar):
    if sym == Lex.var : sym = lex.get(); IdentList( eClass.Par, first)
    else: IdentList( eClass.Var, first)
    if sym == Lex.ident :
        find(obj); sym = lex.get();
        if obj.class_ == eClass.Type : tp = obj.type 
        else: mark( 'type?'); tp = intType 
    else: mark( 'ident?'); tp = intType
    if first.class_ == eClass.Var :
        parsize = tp.size;
        if tp.form >= eForm.Array : mark( 'no struct params') 
    else: parsize = WordSize
    obj = first;
    while obj != NIL :
        nofpar += 1; obj.type = tp; obj.lev = level; obj.value = adr; adr = adr + parsize;
        obj = obj.next 
    return sym

def ProcedureDecl( sym):
    global level;
    marksize = 4;
    # ProcedureDecl  
    sym = lex.get();
    if sym == Lex.ident :
        procid = Lex.id
        obj = NewObj( lex.value, proc, eClass.Proc); sym = lex.get()
        parblksize = marksize
        nofpar = 0
        OpenScope( 'procedure')  
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
        locblksize = parblksize; proc.type = None; proc.dsc = topScope.next; proc.nofpar = nofpar;
        sym = Check( sym, Lex.semicolon, '; expected');
        sym = Declarations( sym, locblksize); proc.dsc = topScope.next;
        while sym == Lex.procedure :
            sym = ProcedureDecl( sym); sym = Check( sym, Lex.semicolon, '; expected')   
        proc.val = osg.pc; gen.Enter( parblksize, locblksize);
        if sym == Lex.begin : sym = lex.get(); sym = StatSequence( sym) 
        sym = Check( sym, Lex.end, 'no END')
        if sym == Lex.ident :
            if procid != Lex.id : mark('no match') 
            sym = lex.get()   
        gen.Return( locblksize)
        level -= 1; 
        CloseScope()
    return sym

def Module( sym):
    global level
    if sym == Lex.module_ :
        sym = lex.get();
        if sym == Lex.times : 
            tag = 1
            sym = lex.get() 
        else: tag = 0 
        gen.Open()
        OpenScope( 'module')
        dc = 0
        level = 0
        if sym == Lex.ident :
            modid = lex.value; 
            sym = lex.get()
            print 'Compiling module:', modid
        else: mark('ident?')
        sym = Check( sym, Lex.semicolon, '; expected')
        sym, dc = Declarations( sym, dc)
        while sym == Lex.procedure : sym = ProcedureDecl( sym); sym = Check( sym, Lex.semicolon, '; expected') 
        gen.Header( dc);
        if sym == Lex.begin : sym = lex.get(); sym = StatSequence( sym) 
        sym = Check( sym, Lex.end, 'no END')
        if sym == Lex.ident :
            if modid != lex.value : Lex.mark( 'no match') 
            sym = lex.get()
        else: mark( 'ident?')      
        if sym != Lex.period : mark('. ?') 
        # universeView() # dbg        
        CloseScope()
        if  getErrcnt() == 0 :
            gen.Close() 
            print '\r\nCode generated:', gen.pc, '\tdata:', dc
            return True
        else: 
            mark('MODULE?')
            return False

def Compile():
    sym = lex.get()
    return Module( sym) 

def addBuiltin( name, cl, value, type):
    obj = NewObj( name, cl)
    obj.value = value
    obj.type = type

def universeView():
    print
    for scope in universe:
        print scope.name
        for i, ident in enumerate( scope.idents):
            print '<',i,'>', ident

def parse( instream):
    global universe, topScope, level, lex
    print 'Oberon-0 Compiler'
    print
    lex = Lexer( instream)
    universe = []; topScope = 0 
    level = 0
    OpenScope( 'root')
    addBuiltin( 'eot', eClass.SFunc, 1, boolType)
    addBuiltin( 'ReadInt', eClass.SProc, 0, None)
    addBuiltin( 'WriteInt', eClass.SProc, 1, None)
    addBuiltin( 'WriteChar', eClass.SProc, 2, None)
    addBuiltin( 'WriteLn', eClass.SProc, 3, None)
    addBuiltin( 'ORD', eClass.SFunc, 0, intType)
    addBuiltin( 'BOOLEAN', eClass.Typ, 0, boolType)
    addBuiltin( 'INTEGER', eClass.Typ, 1, intType)
    return Compile()

lex = None
universe = []; topScope = 0 
level = 0
gen = Osg()
boolType = osg.TypeDesc( 'Bool', form = eForm.Boolean, size = 4)
intType  = osg.TypeDesc( 'Integer', form = eForm.Integer, size = 4)
dummy    = osg.ObjDesc( 'dummy', osg.eClass.Var); dummy.type = intType

if __name__ == '__main__':
    test = '''
    MODULE Test;  
    TYPE 
        c = INTEGER;
    VAR 
        a: c; 
    BEGIN 
        a := 1;
        WriteInt( a);  
    END Test.
    '''
    if parse( iter( test)) :
        gen.Decode()


