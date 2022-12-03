import time
from roboclaw import Roboclaw
try:  # if on win32 or linux
    from serial import SerialException, Serial as UART
except ImportError:
    try:  # try CircuitPython
        from board import UART
    except ImportError:
        try:  # try MicroPythom
            from roboclaw.usart_serial_ctx import SerialUART as UART

# Windows comport name
# rc = Roboclaw(UART("COM3", 115200))
# Linux comport name
# rc = Roboclaw(UART("/dev/ttyACM0", 115200))
# if CircuitPython or MicroPythom
rc = Roboclaw(UART(), address=0x80)

rc.forward_mixed(0)
rc.turn_right_mixed(0)


def test(loop=2):
    while loop:
        rc.forward_mixed(32)
        time.sleep(2)
        rc.backward_mixed(32)
        time.sleep(2)
        rc.turn_right_mixed(32)
        time.sleep(2)
        rc.turn_left_mixed(32)
        time.sleep(2)
        rc.forward_mixed(0)
        rc.turn_right_mixed(32)
        time.sleep(2)
        rc.turn_left_mixed(32)
        time.sleep(2)
        rc.turn_right_mixed(0)
        time.sleep(2)
        loop -= 1
