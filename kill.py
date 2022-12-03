from serial import Serial
from roboclaw import Roboclaw

serial_kick = Serial('/dev/ttyS1', 38400)
serial_wheels = Serial('/dev/ttyUSB0', 38400)

rclaw_kick = Roboclaw(serial_kick)
rclaw_wheels = Roboclaw(serial_wheels)

rclaw_wheels.forward_m1(0)
rclaw_wheels.forward_m2(0)
rclaw_kick.forward_m1(0)
rclaw_kick.forward_m2(0) 
