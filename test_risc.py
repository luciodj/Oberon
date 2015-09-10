#!/usr/bin/env python
import risc
import osg

def ror( x, bits):
    temp = x & ((1<<bits)-1)
    return ((x >> bits ) & ( (1<<(32-bits))-1)) | ( temp << (32-bits))


# print hex( ror( 0x10, 1))
# print hex( ror( 0x12, 32))

def test_print():
    'test the print traps'
    mcu = risc.Risc()
    g = osg.Osg()

    g.Put1( osg.Mov,  1, 0, ord('*'))   # movi R1, '*'
    g.Put1( osg.Mov,  2, 0, -8 )    # movi R2, -8 (printchar_code)
    g.Put2( osg.Stw,  1, 2,  0)     # stw  R1, R2 (print_char R1) 
    g.Put3( osg.BR, 7, -4*4)         # goto 0?
    mcu.run( g.code, 4)
    assert mcu.R[1] == ord('*')
    assert mcu.R[2] == -8 
