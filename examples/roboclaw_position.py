# ***Before using this example the motor/controller combination must be
# ***tuned and the settings saved to the Roboclaw using IonMotion.
# ***The Min and Max Positions must be at least 0 and 50000

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


def displayspeed():
    enc1 = rc.read_encoder_m1()
    enc2 = rc.read_encoder_m2()
    speed1 = rc.read_speed_m1()
    speed2 = rc.read_speed_m2()

    print("Encoder1:")
    if enc1[0] == 1:
        print(enc1[1])
        print(format(enc1[2], '02x'))
    else:
        print("failed")
    print("Encoder2:")
    if enc2[0] == 1:
        print(enc2[1])
        print(format(enc2[2], '02x'))
    else:
        print("failed ")
    print("Speed1:")
    if speed1[0]:
        print(speed1[1])
    else:
        print("failed")
    print("Speed2:")
    if speed2[0]:
        print(speed2[1])
    else:
        print("failed ")


while 1:
    print("Pos 50000")
    rc.speed_accel_deccel_position_m1(32000, 12000, 32000, 50000, 0)
    for i in range(0, 80):
        displayspeed()
        time.sleep(0.1)

    time.sleep(2)

    print("Pos 0")
    rc.speed_accel_deccel_position_m1(32000, 12000, 32000, 0, 0)
    for i in range(0, 80):
        displayspeed()
        time.sleep(0.1)

    time.sleep(2)
