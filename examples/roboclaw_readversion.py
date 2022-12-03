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
        # Get version string
    version = rc.read_version()
    if version[0] == False:
        print("GETVERSION Failed")
    else:
        print(repr(version[1]))
    time.sleep(1)
