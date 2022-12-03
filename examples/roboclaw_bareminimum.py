"""bare minimum example shows you """
from roboclaw import Roboclaw
try:  # if on win32 or linux
    from serial import Serial as UART
except ImportError:
    try:  # try CircuitPython
        from board import UART
    except ImportError:  # try MicroPythom
        from roboclaw.usart_serial_ctx import SerialUART as UART

# Windows comport name
rc = Roboclaw(UART("COM10", 38400))
# Linux comport name
# rc = Roboclaw(UART("/dev/ttyACM0", 38400))
# if CircuitPython or MicroPythom
# rc = Roboclaw(UART(rate=38400))
