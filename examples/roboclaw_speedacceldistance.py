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


version = rc.read_version()
if version[0] == False:
    print("GETVERSION Failed")
else:
    print(repr(version[1]))

while 1:
    rc.speed_accel_distance_m1(12000, 12000, 42000, 1)
    rc.speed_accel_distance_m2(12000, -12000, 42000, 1)

    # distance travelled is v*v/2a = 12000*12000/2*48000 = 1500
    rc.speed_accel_distance_m1(12000, 0, 0, 0)

    # that makes the total move in one direction 48000
    rc.speed_accel_distance_m2(12000, 0, 0, 0)

    buffers = (0, 0, 0)

    # Loop until distance command has completed
    while(buffers[1] != 0x80 and buffers[2] != 0x80):
        print("Buffers: ")
        print(buffers[1])
        print(" ")
        print(buffers[2])
        displayspeed()
        buffers = rc.ReadBuffers()

    time.sleep(1)

    rc.speed_accel_distance_m1(48000, -12000, 46500, 1)
    rc.speed_accel_distance_m2(48000, 12000, 46500, 1)

    # distance travelled is v*v/2a = 12000*12000/2*48000 = 1500
    rc.speed_accel_distance_m1(48000, 0, 0, 0)
    # that makes the total move in one direction 48000
    rc.speed_accel_distance_m2(48000, 0, 0, 0)

    buffers = (0, 0, 0)
    # Loop until distance command has completed
    while(buffers[1] != 0x80 and buffers[2] != 0x80):
        print("Buffers: ")
        print(buffers[1])
        print(" ")
        print(buffers[2])
        displayspeed()
        buffers = rc.read_buffer_length()

    # When no second command is given the motors will automatically slow down to 0 which takes 1 second
    time.sleep(1)
