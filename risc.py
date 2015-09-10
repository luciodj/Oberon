#!/usrbin/env python
'''
  MODULE RISC;  (* NW 22.9.07 / 15.12.2013 *)
'''
import time

MEMLEN = 1024  # in words
REGNUM = 16     
OPCNUM = 16
REGMASK = (REGNUM) - 1
OPCMASK = (OPCNUM) - 1
BYTEMASK = 0xFF
IMMMASK = (1<<16) - 1
OFFMASK = (1<<20) - 1
JMPMASK = (1<<24) - 1

FP   = 13
SP   = 14
LNK  = 15
ZERO = 0 

def ror( x, bits):
    temp = x & ((1<<bits)-1)
    return ((x >> bits ) & ( (1<<(32-bits))-1)) | ( temp << (32-bits))


class Risc:
    MOV = 0; LSL = 1; ASR = 2; ROR = 3; AND = 4; ANN = 5; IOR = 6; XOR = 7
    ADD = 8; SUB = 9;  MUL = 10; DIV = 11
    # condition codes
    MI = 0; EQ = 1; LS = 5; LE = 6; TR = 7; NE = 9; GE = 13; GT = 14 

    R = [ 0 for x in xrange( REGNUM)]   # 32-bit registers
    # pq
    # 00uv |  a(4) | b(4) | opcode(4) |  xxxx  | c(4) |  # a = opcode( b, c)
    # 01uv |  a(4) | b(4) | opcode(4) |     imm(16)   |  # a = opcode( b, imm)
    # 10uv |  a(4) | b(4) |                 off(20)   |  # load / store
    # 11uv |cond(4)|         imm(24)                  |  # a = br(cond, imm)

    def put( self, pquv, op, a, b, c):
        return (pquv << 28) | (a << 24) | (b << 20) | (op << 16) | c

    def printState( self, pc):
        print 'pc=', hex(pc) , 
        print 'SP=', self.R[14],
        print 'FP=', self.R[13],
        print 'R0=', hex(self.R[0]),
        print 'R1=', hex(self.R[1]), 
        print 'R2=', hex(self.R[2])

    def run( self, M, size):
        pc = 0
        self.R[ SP] = len( M)
        self.R[ FP] = size
        H = N = Z = 0
        EOF = False
        print 'RUN:'
        while True: 
            # self.printState( pc) # dbg
            time.sleep(.25)
            ir = M[ pc] 
            pc += 1
            p = (ir >> 31) & 1
            q = (ir >> 30) & 1
            u = (ir >> 29) & 1
            v = (ir >> 28) & 1
            a =  ( ir >> 24) & REGMASK
            b =  ( ir >> 20) & REGMASK
            op = ( ir >> 16) & OPCMASK
            im = ir & IMMMASK

            if p == 0 :  # register instructions       
                B = self.R[b]
                if q == 0 : 
                    C = self.R[ ir & REGMASK]    # group 00
                elif v == 0 : 
                    C = im                                      # not sign extended
                else:       
                    C = im - 0x10000 if im > 0x8000 else  im   # sign extension 
                if   op == self.MOV: A = C if u == 0 else H 
                elif op == self.LSL: A = B << C
                elif op == self.ASR: A = B >> C
                elif op == self.ROR: A = ror (B, C)
                elif op == self.AND: A = B & C
                elif op == self.ANN: A = B & ~C
                elif op == self.IOR: A = B | C
                elif op == self.XOR: A = B ^ C
                elif op == self.ADD: A = B + C ; #print '(A, B, C)', A, B, C
                elif op == self.SUB: A = B - C
                elif op == self.MUL: A = B * C
                elif op == self.DIV: A = B / C; H = B % C
                self.R[a] = A; N = (A < 0); Z = (A == 0)

            elif q == 0 :       # memory load / store
                off = ir & OFFMASK; 
                adr = ( self.R[b] + off)
                if u == 0 : 
                    if adr >= 0:  # load
                        self.R[a] = M[ adr]; 
                    else:  # input
                        if adr == -4 : # hex input 
                            s = raw_input( '>'); 
                            try: self.R[a] = int( s, base=16)
                            except ValueError: self.R[a] = 0; EOF = True
                        elif adr == -8 : # test eof
                            Z = EOF
                else:
                    if adr >= 0 : # store
                        M[ adr] = self.R[a]
                    else: # output
                        if   adr == -4 : print '>', hex( self.R[a]),
                        elif adr == -8 : print chr( self.R[a] & 0x7F),
                        elif adr == -12 : print '\n>'

            else:               # branch instructions
                if  (a == self.MI) and N or (a == self.EQ) and Z or (a == self.LS) and N or (a == self.LE) and (N or Z) or (a == self.TR) or \
                    (a == self.NE) and not Z or (a == self.GE) and not N or (a == self.GT) and not (N or Z) : #(a == self.NE) and not N or 
                    if v == 1 :  self.R[LNK] = pc  * 4 
                    if u == 1 :  
                        rel = ir & OFFMASK
                        if rel & (1<<19) : rel = rel - (1<<20)
                        pc = pc + rel 
                    else: 
                        pc = self.R[ ir & REGMASK] / 4
            if pc == 0: print '\nSTOP'; return
  


