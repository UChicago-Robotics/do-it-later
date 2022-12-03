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

while 1:
    rc.forward_m1(32)  # 1/4 power forward
    rc.backward_m2(32)  # 1/4 power backward
    time.sleep(2)

    rc.backward_m1(32)  # 1/4 power backward
    rc.forward_m2(32)  # 1/4 power forward
    time.sleep(2)

    rc.backward_m1(0)  # Stopped
    rc.forward_m2(0)  # Stopped
    time.sleep(2)

    m1duty = 16
    m2duty = -16
    rc.forward_backward_m1(64+m1duty)  # 1/4 power forward
    rc.forward_backward_m2(64+m2duty)  # 1/4 power backward
    time.sleep(2)

    m1duty = -16
    m2duty = 16
    rc.forward_backward_m1(64+m1duty)  # 1/4 power backward
    rc.forward_backward_m2(64+m2duty)  # 1/4 power forward
    time.sleep(2)

    rc.forward_backward_m1(64)  # Stopped
    rc.forward_backward_m2(64)  # Stopped
    time.sleep(2)
