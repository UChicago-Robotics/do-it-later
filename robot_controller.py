import zmq
import json
from serial import Serial
from roboclaw import Roboclaw
from time import sleep
import signal

class RobotController:
    def __init__(self, host, port):
        print(f"Listening on {host} : {port}")

        context = zmq.Context()
        self.socket = context.socket(zmq.REP)
        self.socket.bind(f"tcp://{host}:{port}")
        
        serial_kick = Serial('/dev/ttyS1', 38400)
        serial_wheels = Serial('/dev/ttyUSB0', 38400)

        self.rclaw_kick = Roboclaw(serial_kick)
        self.rclaw_wheels = Roboclaw(serial_wheels)
        
        self.prev_command = None

    def execute(self, controller_state: str):
        cs = controller_state.replace("\\", "").strip("\"")
        cjson = {k: int(v) for (k, v) in dict(json.loads(cs)).items()}
        
        right_stick = cjson["right_stick_y"]
        left_stick = 127 - cjson["left_stick_y"]
        right_trigger = cjson["right_trigger"]
        left_trigger = cjson["left_trigger"]

        if self.prev_command == None:
            self.prev_command = cjson
        
        # power the wheels based on tank controls
        self.rclaw_wheels.forward_backward_m1(right_stick)
        self.rclaw_wheels.forward_backward_m2(left_stick)
        
        # Check if trigger state has changed because running commands over the 
        # USB bus is expensive
        if (right_trigger, left_trigger) != (self.prev_command["right_trigger"], self.prev_command["left_trigger"]):
            rclaw_kick_target = min(64 + 64 * (left_trigger - right_trigger), 127)
            self.rclaw_kick.forward_backward_m1(rclaw_kick_target)
            self.rclaw_kick.forward_backward_m1(rclaw_kick_target)

        self.prev_command = cjson

    def listen(self):
        while True: 
            controller_state = self.socket.recv_string()
            controller_state.replace("\\", "")

            self.execute(controller_state)
            self.socket.send_string(f"Done")

    def motor_kill(self):
        self.rclaw_wheels.forward_m1(0)
        self.rclaw_wheels.forward_m2(0)
        self.rclaw_kick.forward_m1(0)
        self.rclaw_kick.forward_m2(0) 
        sleep(1)

    def __call__(self):
        pass

def main():
    r = RobotController("*", 5555)
    signal.signal(signal.SIGINT, r.motor_kill)

    r.listen()
    r.motor_kill()

if __name__ == "__main__":
    main()
