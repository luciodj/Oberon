#!/usr/bin/env python
'''
  MODULE OSP; (* NW 23.9.93 / 20.10.07 / 30.10.2013 *)
'''
import oss
import risc
import osg


# expression1: def (VAR x: osg.Item);  #to avoid forward reference

def NewObj( class_): # -> objDesc
    id_ = lex.value
    scope = topScope[0]
    for ident in scope.idents:
        if ident.name == id_ : 
            oss.mark( 'multiple definitions')
            return item
    new = osg.ObjDesc( class_=class_, name=id_, idents=[], type=None, val=0, nofpar=0)
    scope.idents.append( new) 
    return new

def find( id_): 
    for scope in topScope:
        for x in scope.idList:
            if x.name == id_: return x 
    else:  
        oss.mark('undefined'); return dummy 

def FindField( id_, lst):
    for x in lst: 
        if x.name == id_ : return x
    else: 
        oss.mark( 'undefined'); return dummy 

def Check( sym, s, msg):
    if sym == s : return oss.get() 
    else: oss.mark( msg) 

def CheckInt( x): # osg.Item
    if x.type.form != osg.Integer : oss.mark('not integer') 

def CheckBool( x): # osg.Item
    if x.type.form != osg.Boolean : oss.mark('not Boolean') 

def OpenScope( name):
    scope = osg.ObjScope( name=name, idents=[])
    topScope.insert( 0, scope) 
     
def CloseScope():
    topScope.pop(0)

# -------------------- Parser ---------------------

def selector( sym, x): # osg.Item
    while ( sym == oss.lbrak) or ( sym == oss.period) :
        if sym == oss.lbrak :
            sym, y = expression1( oss.get())
            if x.type.form == osg.Array :
                CheckInt( y); osg.Index( x, y); x.type = x.type.base
            else: oss.mark('not an array')          
            Check( sym, oss.rbrak, 'no ]')
        else: # period 
            sym, id_ = oss.get()
            if sym == oss.ident :
                if x.type.form == osg.Record :
                    obj = FindField( id_, x.type.fieldList)
                    sym, val = oss.get()
                    osg.Field( x, obj) 
                    x.type = obj.type 
                else: oss.mark('not a record')
            else: oss.mark( 'ident?')      

def CompTypes( t0, t1): # (osg.Type): # -> BOOLEAN;
    'Compatible Types'
    return (t0 == t1) or \
           (t0.form == osg.Array) and (t1.form == osg.Array) and CompTypes( t0.base, t1.base)


def Parameter( sym, par): # osg.Object
    sym, x = expression( )
    if par :
        varpar = par.class_ == osg.Par
        if CompTypes( par.type, x.type) :
            if not varpar : sym, x = osg.ValueParam( )
            else: sym, x = osg.VarParam( par.type)
        elif ( x.type.form == osg.Array) and (par.type.form == osg.Array) and \
        ( x.type.base.form == par.type.base.form) and (par.type.len < 0) :
            osg.OpenArrayParam( x)
    else: oss.mark('incompatible parameters')
  
def ParamList( obj): # osg.Object
    par = obj.dsc; n = 0;
    if sym != oss.rparen :
        Parameter(par); n = 1;
        while sym <= oss.comma :
            Check( sym, 'comma?')
            if par : par = par.next 
            INC(n); Parameter(par)        
        Check( oss.rparen, ') missing')
    else: oss.get(sym);
    if n < obj.nofpar : oss.mark('too few params')
    elif n > obj.nofpar : oss.mark('too many params')

def StandFunc( x, fctno): #LONGINT
    if sym == oss.lparen :
        oss.get(sym);
        if fctno == 0 : # ORD
            expression1(x); osg.Ord(x)
        elif fctno == 1 : #eot 
            osg.eot(x)      
        if sym == oss.rparen : oss.get(sym) 
        else: oss.mark('rparen expected') 
    else: oss.mark('param missing'); osg.MakeConstItem(x, osg.intType, 0)

def factor( x): # -> osg.Item
    # sync
    if (sym < oss.char) or (sym > oss.ident) : 
        oss.mark('expression expected')
        while True:
           oss.get(sym) 
           if (sym >= oss.int) and (sym <= oss.ident): break
    if sym == oss.ident :
        find(obj); oss.get(sym);
        if obj.class_ == osg.SFunc :
            if obj.type == NIL : oss.mark('not a function'); obj.type = osg.intType 
            StandFunc(x, obj.val); x.type = obj.type
        else: osg.MakeItem(x, obj, level); selector(x)
    elif sym == oss.int : osg.MakeConstItem(x, osg.intType, oss.val); oss.get(sym)
    elif sym == oss.char : osg.MakeConstItem(x, osg.intType, oss.val); oss.get(sym)
    elif sym == oss.lparen :
        oss.get(sym);
        if sym != oss.rparen : expression1(x) 
        Check(oss.rparen, 'no )')
    elif sym == oss.not_ : oss.get(sym); factor(x); CheckBool(x); osg.Not(x)
    elif sym == oss.false : oss.get(sym); osg.MakeConstItem(x, osg.boolType, 0)
    elif sym == oss.true : oss.get(sym); osg.MakeConstItem(x, osg.boolType, 1)
    else: oss.mark( 'factor?'); osg.MakeItem(x, dummy, level)

def term( x): # osg.Item
    factor(x);
    while (sym >= oss.times) and (sym <= oss.and_) :
        op = sym; oss.get(sym);
        if op == oss.times : 
            CheckInt(x); factor(y); CheckInt(y); osg.MulOp(x, y)
        elif (op == oss.div) or (op == oss.mod) : 
            CheckInt(x); factor(y); CheckInt(y); osg.DivOp(op, x, y)
        else: #op = and
            CheckBool(x); osg.And1(x); factor(y); CheckBool(y); osg.And2(x, y)

def SimpleExpression( x): # osg.Item
    if sym == oss.plus : oss.get(sym); term(x); CheckInt(x)
    elif sym == oss.minus : oss.get(sym); term(x); CheckInt(x); osg.Neg(x)
    else: term(x)
    while (sym >= oss.plus) and (sym <= oss.or_) :
        op = sym; oss.get(sym);
        if op == oss.or_ : osg.Or1(x); CheckBool(x); term(y); CheckBool(y); osg.Or2(x, y)
        else: CheckInt(x); term(y); CheckInt(y); osg.AddOp(op, x, y)

def expression( x): #osg.Item
    SimpleExpression(x);
    if (sym >= oss.eql) and (sym <= oss.geq) :
        op = sym; oss.get(sym); SimpleExpression(y);
        if x.type == y.type : osg.Relation( op, x, y) 
        else: oss.mark('incompatible types') 
        x.type = osg.boolType

def StandProc( pno): #LONGINT
    if sym == oss.lparen :
        oss.get(sym); expression(x);
        if pno == 0 :  osg.ReadInt(x)
        elif pno == 1 : osg.WriteInt(x)
        elif pno == 2 : osg.WriteChar(x)
        elif pno == 3 : osg.WriteLn
    else: 
        oss.mark('no lparen')          
    if sym == oss.rparen : oss.get(sym) 
    else: oss.mark( 'no rparen') 

def StatSequence():
    # StatSequence 
    while True: # sync 
        obj = NIL;
        if not ((sym == oss.ident) or (sym >= oss.if_) and (sym <= oss.repeat) or (sym >= oss.semicolon)) :
            oss.mark('statement expected');
            while True: 
                oss.get(sym) 
                if (sym == oss.ident) or (sym >= oss.if_): break  
        if sym == oss.ident :
            find(obj); oss.get(sym)
            if obj.class_ == osg.SProc : StandProc( obj.val)
            else: osg.MakeItem(x, obj, level); selector(x);
            if sym == oss.becomes : #assignment*)
                oss.get(sym); expression(y);
                if (x.type.form in [osg.Boolean, osg.Integer]) and (x.type.form == y.type.form) : osg.Store(x, y)
                else: oss.mark('incompatible assignment')
            elif sym == oss.eql : oss.mark('should be =='); oss.get(sym); expression(y)
            elif sym == oss.lparen : #procedure call*)
                oss.get(sym);
                if (obj.class_ == osg.Proc) and (obj.type == NIL) : ParamList(obj); osg.Call(obj);
                else: oss.mark('not a procedure')
            elif obj.class_ == osg.Proc : #procedure call without parameters*)
                if obj.nofpar > 0 : oss.mark('missing parameters') 
                if not obj.type : osg.Call(obj) 
                else: oss.mark('not a procedure') 
            elif (obj.class_ == osg.SProc) and (obj.val == 3) : osg.WriteLn
            elif obj.class_ == osg.Typ : oss.mark('illegal assignment')
            else: oss.mark('not a procedure')
        elif sym == oss.if_ :
            oss.get(sym); expression(x); CheckBool(x); osg.CFJump(x); Check(oss.then, 'no :')
            StatSequence; L = 0;
            while sym == oss.elsif :
                oss.get(sym); osg.FJump(L); osg.FixLink(x.a); expression(x); CheckBool(x); osg.CFJump(x);
                if sym == oss.then : oss.get(sym) 
                else: oss.mark(':?') 
                StatSequence
            if sym == oss.else_ :
                oss.get(sym); osg.FJump(L); osg.FixLink(x.a); StatSequence
            else: osg.FixLink(x.a)    
            osg.FixLink(L);
            if sym == oss.end : oss.get(sym) 
            else: oss.mark('END?') 
        elif sym == oss.while_ :
            oss.get(sym); L = osg.pc; expression(x); CheckBool(x); osg.CFJump(x);
            Check(oss.do, 'no :'); StatSequence; osg.BJump(L); osg.FixLink(x.a);
            Check(oss.end, 'no END')
        elif sym == oss.repeat :
            oss.get(sym); L = osg.pc; StatSequence;
            if sym == oss.until :
                oss.get(sym); expression(x); CheckBool(x); osg.CBJump(x, L)
            else: oss.mark('missing UNTIL'); oss.get(sym)  
        osg.CheckRegs;
        if sym == oss.semicolon : oss.get( sym)
        elif sym < oss.semicolon : oss.mark( 'missing semicolon?')
        if sym > oss.semicolon: break

def IdentList(class_, first):
    if sym == oss.ident :
        NewObj(first, class_); oss.get(sym);
        while sym == oss.comma :
            oss.get(sym);
            if sym == oss.ident : NewObj(obj, class_); oss.get(sym)
            else: oss.mark('ident?')
        Check( oss.colon, 'no :')

def Type( type): # osg.Type);
    type = osg.intType; #sync*)
    if (sym != oss.ident) and (sym < oss.array) : 
        oss.mark('type?');
        while True: 
            oss.get(sym) 
            if (sym == oss.ident) or (sym >= oss.array) : break
    if sym == oss.ident :
        find(obj); oss.get(sym);
        if obj.class_ == osg.Typ : type = obj.type 
        else: oss.mark('type?') 
    elif sym == oss.array :
        oss.get(sym); expression(x);
        if (x.mode != osg.Const) or (x.a < 0) : oss.mark('bad index') 
        if sym == oss.of : oss.get(sym) 
        else: oss.mark('OF?') 
        Type(tp); NEW(type); type.form = osg.Array; type.base = tp;
        type.len = x.a; type.size = type.len * tp.size
    elif sym == oss.record :
        oss.get(sym); NEW(type); type.form = osg.Record; type.size = 0; OpenScope;
        while True:
            if sym == oss.ident :
                IdentList(osg.Fld, first); Type(tp); obj = first;
                while obj != NIL :
                    obj.type = tp; 
                    obj.val = type.size; 
                    type.size = type.size + obj.type.size; 
                    obj = obj.next                  
            if sym == oss.semicolon : oss.get(sym)
            elif sym == oss.ident : oss.mark('; ?')
            if sym != oss.ident: break
        type.dsc = topScope.next; 
        CloseScope; 
        Check(oss.end, 'no END')
    else: oss.mark('ident?')  

def Declarations( varsize): #LONGINT
    # sync
    if (sym < oss.const) and (sym != oss.end) : 
        oss.mark('declaration?');
        while True: 
            oss.get(sym) 
            if (sym >= oss.const) or (sym == oss.end): break
    if sym == oss.const :
        oss.get(sym);
        while sym == oss.ident :
            NewObj(obj, osg.Const); oss.get(sym);
            if sym == oss.eql : oss.get(sym) 
            else: oss.mark('=?') 
            expression(x);
            if x.mode == osg.Const : obj.val = x.a; obj.type = x.type
            else: oss.mark('expression not constant')      
            Check(oss.semicolon, '; expected')
    if sym == oss.type :
        oss.get(sym);
        while sym == oss.ident :
            NewObj(obj, osg.Typ); oss.get(sym);
            if sym == oss.eql : oss.get(sym) 
            else: oss.mark('=?')  
            Type(obj.type); Check(oss.semicolon, '; expected')
    if sym == oss.var :
        oss.get(sym);
        while sym == oss.ident :
            IdentList(osg.Var, first); Type(tp);
            obj = first;
            while obj != NIL :
                obj.type = tp; obj.lev = level;
                obj.val = varsize; varsize = varsize + obj.type.size; obj = obj.next
            Check(oss.semicolon, '; expected')
    if (sym >= oss.const) and (sym <= oss.var) : oss.mark('declaration in bad order') 


def FPSection( adr, nofpar):
    if sym == oss.var : oss.get(sym); IdentList(osg.Par, first)
    else: IdentList(osg.Var, first)
    if sym == oss.ident :
        find(obj); oss.get(sym);
        if obj.class_ == osg.Typ : tp = obj.type 
        else: oss.mark('type?'); tp = osg.intType 
    else: oss.mark('ident?'); tp = osg.intType
    if first.class_ == osg.Var :
        parsize = tp.size;
        if tp.form >= osg.Array : oss.mark('no struct params') 
    else: parsize = WordSize
    obj = first;
    while obj != NIL :
        INC(nofpar); obj.type = tp; obj.lev = level; obj.val = adr; adr = adr + parsize;
        obj = obj.next 


def ProcedureDecl():
    marksize = 4;
    # ProcedureDecl  
    oss.get(sym);
    if sym == oss.ident :
        procid = oss.id;
        NewObj(proc, osg.Proc); oss.get(sym); parblksize = marksize; nofpar = 0;
        OpenScope;  INC(level); proc.val = -1;
        if sym == oss.lparen :
            oss.get(sym);
            if sym == oss.rparen : oss.get(sym)
            else: 
                FPSection(parblksize, nofpar);
                while sym == oss.semicolon : oss.get(sym); FPSection(parblksize, nofpar) 
                if sym == oss.rparen : oss.get(sym) 
                else: oss.mark(')?')
        locblksize = parblksize; proc.type = NIL; proc.dsc = topScope.next; proc.nofpar = nofpar;
        Check(oss.semicolon, '; expected');
        Declarations(locblksize); proc.dsc = topScope.next;
        while sym == oss.procedure :
            ProcedureDecl; Check(oss.semicolon, '; expected')   
        proc.val = osg.pc; osg.Enter(parblksize, locblksize);
        if sym == oss.begin : oss.get(sym); StatSequence 
        Check(oss.end, 'no END')
        if sym == oss.ident :
            if procid != oss.id : oss.mark('no match') 
            oss.get(sym)   
        osg.Return(locblksize)
        level -= 1; 
        CloseScope()

def Module():
    Texts.WriteString(W, 'compiling ');
    if sym == oss.module :
        oss.get(sym);
        if sym == oss.times : tag = 1; oss.get(sym) 
        else: tag = 0 
        osg.Open; OpenScope; dc = 0; level = 0;
        if sym == oss.ident :
            modid = oss.id; oss.get(sym);
            Texts.WriteString(W, modid); Texts.WriteLn(W); Texts.Append(Oberon.Log, W.buf)
        else: oss.mark('ident?')
        Check(oss.semicolon, '; expected');
        Declarations(dc);
        while sym == oss.procedure : ProcedureDecl; Check(oss.semicolon, '; expected') 
        osg.Header(dc);
        if sym == oss.begin : oss.get(sym); StatSequence 
        Check(oss.end, 'no END');
        if sym == oss.ident :
            if modid != oss.id : oss.mark('no match') 
            oss.get(sym)
        else: oss.mark('ident?')      
        if sym != oss.period : oss.mark('. ?') 
        CloseScope;
        if not oss.error :
            osg.Close; Texts.WriteString(W, 'code generated');
            print osg.pc, dc
        else: oss.mark('MODULE?')

def Compile():
    Oberon.GetSelection(T, beg, end, time);
    if time >= 0 : oss.Init(T, beg); oss.get(sym); 
    Module() 

def addBuiltin( name, cl, value, type):
    obj = NewObj( class_ = cl)
    obj.val = value
    obj.name = name
    obj.type = type
    obj.next = topScope.next; topScope.next = obj

# def init():
if __name__ == '__main__':            
    print 'Oberon-0 Compiler OSP  30.10.2013'
    print
    lex = oss.Lexer( iter( 'MODULE;'))
    dummy = osg.ObjDesc( name='dummy', class_=osg.eClass.Var, type=osg.Osg.intType, val=0, nofpar=0, idents=[])
    topScope = [] 
    OpenScope( 'root')
    expression1 = expression
    addBuiltin('eot', osg.eClass.SFunc, 1, osg.Osg.boolType);
    addBuiltin('ReadInt', osg.SProc, 0, NIL);
    addBuiltin('WriteInt', osg.SProc, 1, NIL);
    addBuiltin('WriteChar', osg.SProc, 2, NIL);
    addBuiltin('WriteLn', osg.SProc, 3, NIL);
    addBuiltin('ORD', osg.SFunc, 0, osg.Osg.intType);
    addBuiltin('BOOLEAN', osg.Typ, 0, osg.Osg.boolType);
    addBuiltin('INTEGER', osg.Typ, 1, osg.Osg.intType);
    universe = topScope
