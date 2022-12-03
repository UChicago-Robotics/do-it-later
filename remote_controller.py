import pygame as pg
import traceback
import math
import json
import zmq
import time
import json

ip = "192.168.8.232"
port = 5555

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect(f"tcp://{ip}:{port}")
print(f"Connected to {ip} {port}")

# checking the pygame version because they behave different
version = pg.__version__
PGVERSION = int(version.split('.')[0])

offset_y = 64
WIDTH = 812
HEIGHT = 554 + offset_y

vec = pg.math.Vector2

# initialize pygame
pg.init()
#screen = pg.display.set_mode((WIDTH, HEIGHT))
clock = pg.time.Clock()

pg.joystick.init()

deadzone_stick = 0.2
deadzone_trigger = 0.01

button_a_pos = (584, 201 + offset_y)
button_b_pos = (637, 148 + offset_y)
button_x_pos = (533, 149 + offset_y)
button_y_pos = (585, 96 + offset_y)

button_back_pos = (336, 159 + offset_y)
button_start_pos = (451, 159 + offset_y)

shoulder_l_pos = (123, 4 + offset_y)
shoulder_r_pos = (510, 4 + offset_y)

stick_l = vec(0, 0)
stick_r = vec(0, 0)

stick_l_center = vec(214, 175 + offset_y)
stick_r_center = vec(510, 294 + offset_y)

stick_radius = 30
stick_size = 20

trigger_r = 0
trigger_l = 0


# game loop
running = True
try:
    while running:
        clock.tick(60)

        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False

        # detect gamepad
        gamepads = [pg.joystick.Joystick(x) for x in range(
            pg.joystick.get_count())]
        if len(gamepads) > 0:
            gamepads[0].init()
            axes = gamepads[0].get_numaxes()

            trigger_r = 0
            trigger_l = 0

            # get axes values
            for i in range(axes):
                axis = gamepads[0].get_axis(i)
                if i == 0 and abs(axis) > deadzone_stick:
                    # left stick left/right
                    stick_l.x = axis
                elif i == 1 and abs(axis) > deadzone_stick:
                    # left stick up/down
                    stick_l.y = axis
                elif i == 2 and abs(axis) > deadzone_stick:
                    # right stick left/right
                    stick_r.x = axis
                elif i == 3 and abs(axis) > deadzone_stick:
                    # right stick up/down
                    stick_r.y = axis
                elif i == 4 and axis > deadzone_trigger:
                    # left trigger
                    trigger_l = 1
                elif i == 5 and axis > deadzone_trigger:
                    # right trigger
                    trigger_r = 1

            # draw analog sticks
            # left stick
            draw_stick_l = vec(0, 0)
            draw_stick_l.x = stick_l.x * math.sqrt(1 - 0.5 * stick_l.y ** 2)
            draw_stick_l.y = -stick_l.y * math.sqrt(1 - 0.5 * stick_l.x ** 2)
            if round(draw_stick_l.length(), 1) >= deadzone_stick:
                vec_left = stick_l_center + draw_stick_l * stick_radius
                stick_l = vec(0,0)
            else:
                vec_left = vec(stick_l_center)

            # right stick
            draw_stick_r = vec(0, 0)
            draw_stick_r.x = stick_r.x * math.sqrt(1 - 0.5 * stick_r.y ** 2)
            draw_stick_r.y = -stick_r.y * math.sqrt(1 - 0.5 * stick_r.x ** 2)
            if round(draw_stick_r.length(), 1) >= deadzone_stick:
                vec_right = stick_r_center + draw_stick_r * stick_radius
                stick_r = vec(0,0)
            else:
                vec_right = vec(stick_r_center)

            controls = {
                "left_stick_y": draw_stick_l.y,
                "right_stick_y": draw_stick_r.y,
                "left_trigger": trigger_l,
                "right_trigger": trigger_r
            }

            controls_json = json.dumps(controls)
            socket.send_string(controls_json)

            message = socket.recv_string()
            print(f"Server replied: {message}\n")

        else:
            text = "No Device plugged in."
            print(text)

    pg.quit()
except Exception:
    traceback.print_exc()
    pg.quit()