"""roboclaw driver module contains the roboclaw driver class that controls
the roboclaw via a UART serial"""
import os
from struct import pack, unpack
from .serial_commands import Cmd
from .data_manip import crc16, validate16

# pylint: disable=line-too-long,invalid-name,too-many-function-args,too-many-public-methods

# this function doesn't need a self pointer
def _recv(buf):
    if validate16(buf):
        return buf[:-2]
    return False

class Roboclaw:
    """A driver class for the RoboClaw Motor Controller device.

    :param ~serial.Serial serial_obj: The serial obj associated with the serial port that is connected to the RoboClaw.
    :param int address: The unique address assigned to the particular RoboClaw. Valid addresses range [``0x80``, ``0x87``].
    :param int retries: The amount of attempts to read/write data over the serial port. Defaults to 3.
    """
    def __init__(self, serial_obj, address=0x80, retries=3, packet_serial=True):
        self.serial_obj = serial_obj
        self.serial_obj.close()
        self._retries = retries
        self.packet_serial = packet_serial #: this `bool` represents if using packet serial mode.
        if address not in range(0x80, 0x88):
            raise ValueError('Unsupported specified address: {address}')
        self._address = address

    @property
    def address(self):
        """The Address of the specific Roboclaw device on the object's serial port
        Must be in range [``0x80``, ``0x87``]"""
        return self._address

    @address.setter
    def address(self, addr):
        assert addr in range(0x80, 0x88)
        self._address = addr

    def _send(self, buf, ack=None, address=None, crc=True):
        """
        :param bytearray buf: the message to send (not including address nor CRC16 checksum)
        :param int ack: Expected number of bytes to read in response. `None` reads 1 byte
            (expceted to be ``0xFF``) and returns `True` if successful.
        :param int address: The default `None` value invokes using the internally saved address
            byte (passed to constructor upon instantiation -- defaults to ``0x80``). If using the
            same `Roboclaw` objectfor a different Roboclaw device, pass the address allocated to
            that device (limited to range [``0x80``, ``0x87``]).
        :param bool crc: This boolean is meant to allow a specific command to not need CRC16
            checksum. Leave this parameter alone unless you absolutely know what you're doing.
            To disable the CRC16 checksum usage, you must configure the roboclaw to use "simple
            serial" mode using the Ion Motion Studio software or using `set_config()` and setting
            `packet_serial` to `False`.
        """
        trys = self._retries
        assert address is None or address in range(0x80, 0x88)
        buf = bytes(([self._address] if address is None else [address])) + buf
        if self.packet_serial:
            checksum = crc16(buf)
            buf += bytes([checksum >> 8, checksum & 0xff])
        with self.serial_obj:
            while trys:
                self.serial_obj.write(buf)
                if ack is None: # expects blanket ack
                    response = self.serial_obj.read(1)
                    if response: # if not timeout
                        if unpack('>B', response)[0] == 0xff:
                            return True
                elif not ack:
                    return self.serial_obj.read_until() # special case ack terminated w/ '\n' char
                else: # for passing ack to _recv()
                    return self.serial_obj.read(ack + (2 if self.packet_serial and crc else 0))
                trys -= 1
        return False

    # User accessible functions
    def send_random_data(self, cnt, address=None):
        """Send some randomly generated data of of a certain length. Don't know what this would be used for, but it was in the original driver code...

        :param int cnt: the number of bytes to randomly generate."""
        buf = b''
        for _ in range(cnt):
            buf += pack('>B', os.urandom(1))
        self._send(buf, address=address)

    def forward_m1(self, val, address=None):
        """Drive motor 1 forward.

        :param int val: Valid data range is 0 - 127. A value of 127 = full speed forward, 64 = about half speed forward and 0 = full stop.
        """
        # :Sends: [Address, 0, Value]
        return self._send(pack('>BB', Cmd.M1FORWARD, val), address=address)

    def backward_m1(self, val, address=None):
        """Drive motor 1 backwards.

        :param int val: Valid data range is 0 - 127. A value of 127 full speed backwards, 64 = about half speed backward and 0 = full stop.
        """
        # :Sends: [Address, 1, Value]
        return self._send(pack('>BB', Cmd.M1BACKWARD, val), address=address)

    def set_min_voltage_main_battery(self, val, address=None):
        """Sets main battery (B- / B+) minimum voltage level. If the battery voltages drops below the set voltage level, RoboClaw will stop driving the motors. The voltage is set in .2 volt increments. The minimum value allowed which is 6V.

        :param float val: The valid data range is [6, 34] Volts.
        """
        # :Sends: [Address, 2, Value]
        # translated byte value range = [0, 140]
        # The formula for calculating the voltage is: (Desired Volts - 6) x 5 = Value.
        # Examples of valid values are 6V = 0, 8V = 10 and 11V = 25.
        return self._send(pack('>BB', Cmd.SETMINMB, int(val / 5 + 6)), address=address)

    def set_max_voltage_main_battery(self, val, address=None):
        """Sets main battery (B- / B+) maximum voltage level. During regenerative breaking a back voltage is applied to charge the battery. When using a power supply, by setting the maximum voltage level, RoboClaw will, before exceeding it, go into hard braking mode until the voltage drops below the maximum value set. This will prevent overvoltage conditions when using power supplies.

        :param float val: The valid data range is [6, 34] Volts.
        """
        # :Sends: [Address, 3, Value]
        # translated byte value range = [30, 175]
        # The formula for calculating the voltage is: Desired Volts x 5.12 = Value.
        # Examples of valid values are 12V = 62, 16V = 82 and 24V = 123.
        return self._send(pack('>BB', Cmd.SETMAXMB, int(val / 5.12)), address=address)

    def forward_m2(self, val, address=None):
        """Drive motor 2 forward.

        :param int val: Valid data range is [0, 127]. A value of 127 full speed forward, 64 = about half speed forward and 0 = full stop.
        """
        # :Sends: [Address, 4, Value]
        return self._send(pack('>BB', Cmd.M2FORWARD, val), address=address)

    def backward_m2(self, val, address=None):
        """Drive motor 2 backwards.

        :param int val: Valid data range is [0, 127]. A value of 127 full speed backwards, 64 = about half speed backward and 0 = full stop.
        """
        # :Sends: [Address, 5, Value]
        return self._send(pack('>BB', Cmd.M2BACKWARD, val), address=address)

    def forward_backward_m1(self, val, address=None):
        """Drive motor 1 forward or reverse.

        :param int val: Valid data range is [0, 127]. A value of 0 = full speed reverse, 64 = stop and 127 = full speed forward.
        """
        # :Sends: [Address, 6, Value]
        return self._send(pack('>BB', Cmd.M17BIT, val), address=address)

    def forward_backward_m2(self, val, address=None):
        """Drive motor 2 forward or reverse.

        :param int val: Valid data range is [0, 127]. A value of 0 = full speed reverse, 64 = stop and 127 = full speed forward.
        """
        # :Sends: [Address, 7, Value]
        return self._send(pack('>BB', Cmd.M27BIT, val), address=address)

    def forward_mixed(self, val, address=None):
        """Drive forward in mix mode.

        :param int val: Valid data range is [0, 127]. A value of 0 = full stop and 127 = full forward.
        """
        # :Sends: [Address, 8, Value]
        return self._send(pack('>BB', Cmd.MIXEDFORWARD, val), address=address)

    def backward_mixed(self, val, address=None):
        """Drive backwards in mix mode.

        :param int val: Valid data range is [0, 127]. A value of 0 = full stop and 127 = full reverse.
        """
        # :Sends: [Address, 9, Value]
        return self._send(pack('>BB', Cmd.MIXEDBACKWARD, val), address=address)

    def turn_right_mixed(self, val, address=None):
        """Turn right in mix mode.

        :param int val: Valid data range is [0, 127]. A value of 0 = stop turn and 127 = full speed turn.
        """
        # :Sends: [Address, 10, Value]
        return self._send(pack('>BB', Cmd.MIXEDRIGHT, val), address=address)

    def turn_left_mixed(self, val, address=None):
        """Turn left in mix mode.

        :param int val: Valid data range is [0, 127]. A value of 0 = stop turn and 127 = full speed turn.
        """
        # :Sends: [Address, 11, Value]
        return self._send(pack('>BB', Cmd.MIXEDLEFT, val), address=address)

    def forward_backward_mixed(self, val, address=None):
        """Drive forward or backwards.

        :param int val: Valid data range is [0, 127]. A value of 0 = full backward, 64 = stop and 127 = full forward.
        """
        # :Sends: [Address, 12, Value]
        return self._send(pack('>BB', Cmd.MIXEDFB, val), address=address)

    def left_right_mixed(self, val, address=None):
        """Turn left or right.

        :param int val: Valid data range is [0, 127]. A value of 0 = full left, 64 = stop turn and 127 = full right.
        """
        # :Sends: [Address, 13, Value]
        return self._send(pack('>BB', Cmd.MIXEDLR, val), address=address)

    def read_encoder_m1(self, address=None):
        """Read M1 encoder count/position.

        :Returns: [Enc1(4 bytes), Status, crc16(2 bytes)]

        Quadrature encoders have a range of 0 to 4,294,967,295. Absolute encoder values are converted from an analog voltage into a value from 0 to 4095 for the full 5.1v range.

        The status byte tracks counter underflow, direction and overflow. The byte value represents:

        * Bit0 - Counter Underflow (1= Underflow Occurred, Clear After Reading)
        * Bit1 - Direction (0 = Forward, 1 = Backwards)
        * Bit2 - Counter Overflow (1= Underflow Occurred, Clear After Reading)
        * Bit3 through Bit7 - Reserved
        """
        return unpack('>iB', _recv(self._send(pack('>B', Cmd.GETM1ENC), address=address, ack=5)))

    def read_encoder_m2(self, address=None):
        """ Read M2 encoder count/position.

        :Returns: [EncoderCount(4 bytes), Status]

        Quadrature encoders have a range of 0 to 4,294,967,295. Absolute encoder values are converted from an analog voltage into a value from 0 to 4095 for the full 5.1v range.

        The Status byte tracks counter underflow, direction and overflow. The byte value represents:

        * Bit0 - Counter Underflow (1= Underflow Occurred, Cleared After Reading)
        * Bit1 - Direction (0 = Forward, 1 = Backwards)
        * Bit2 - Counter Overflow (1= Underflow Occurred, Cleared After Reading)
        * Bit3 through Bit7 - Reserved

        """
        return unpack('>IB', _recv(self._send(pack('>B', Cmd.GETM2ENC), address=address, ack=5)))

    def read_speed_m1(self, address=None):
        """Read M1 counter speed. Returned value is in pulses per second. MCP keeps track of how many pulses received per second for both encoder channels.

        :Returns: [Speed(4 bytes), Status]

        Status indicates the direction (0 – forward, 1 - backward).
        """
        return unpack('>IB', _recv(self._send(pack('>B', Cmd.GETM1SPEED), address=address, ack=5)))

    def read_speed_m2(self, address=None):
        """Read M2 counter speed. Returned value is in pulses per second. MCP keeps track of how many pulses received per second for both encoder channels.

        :Returns: [Speed(4 bytes), Status]

        Status indicates the direction (0 – forward, 1 - backward).
        """
        return unpack('>IB', _recv(self._send(pack('>B', Cmd.GETM2SPEED), address=address, ack=5)))

    def reset_encoders(self, address=None):
        """Will reset both quadrature decoder counters to zero. This command applies to quadrature encoders only."""
        return self._send(pack('>B', Cmd.RESETENC), address=address)

    def read_version(self, address=None):
        """Read RoboClaw firmware version. Returns up to 48 bytes(depending on the Roboclaw model) and is terminated by a line feed character and a null character.

        :Returns: ["MCP266 2x60A v1.0.0",10,0]

        The command will return up to 48 bytes. The return string includes the product name and firmware version. The return string is terminated with a line feed (10) and null (0) character.
        """
        version = _recv(self._send(pack('>B', Cmd.GETVERSION), address=address, ack=0))
        if version:
            return ''.join(chr(c) for c in version[:-2])
        return 'Unknown. Read command failed'

    def set_enc_m1(self, cnt, address=None):
        """Set the value of the Encoder 1 register. Useful when homing motor 1. This command applies to quadrature encoders only."""
        return self._send(pack('>BI', Cmd.SETM1ENCCOUNT, cnt), address=address)

    def set_enc_m2(self, cnt, address=None):
        """Set the value of the Encoder 2 register. Useful when homing motor 2. This command applies to quadrature encoders only."""
        return self._send(pack('>BI', Cmd.SETM2ENCCOUNT, cnt), address=address)

    def read_main_battery_voltage(self, address=None):
        """Read the main battery voltage level connected to B+ and B- terminals.

        :Returns: The voltage is returned in 10ths of a volt (eg 30.0).
        """
        # :Returns: [Value(2 bytes)]The voltage is returned in 10ths of a volt(eg 300 = 30v).
        return unpack('>h', _recv(self._send(pack('>B', Cmd.GETMBATT), address=address, ack=2)))[0] / 10

    def read_logic_battery_voltage(self, address=None):
        """Read a logic battery voltage level connected to LB+ and LB- terminals. The voltage is returned in 10ths of a volt(eg 50 = 5v).

        :Returns: [Value.Byte1, Value.Byte0]
        """
        data = unpack('>BB', _recv(self._send(pack('>B', Cmd.GETLBATT), address=address, ack=2)))
        if data:
            return data
        return (0, 0)

    def set_min_voltage_logic_battery(self, val, address=None):
        """
        Sets logic input (LB- / LB+) minimum voltage level. RoboClaw will shut down with an error if the voltage is below this level. The voltage is set in .2 volt increments. The minimum value allowed which is 6V.

        :param float val: The valid data range is [6, 34].

        .. note:: This command is included for backwards compatibility. We recommend you use `set_logic_voltages()` instead.
        """
        # translated byte value range = [0, 140]
        # The formula for calculating the voltage is: (Desired Volts - 6) x 5 = Value.
        # Examples of valid values are 6V = 0, 8V = 10 and 11V = 25.
        return self._send(pack('>BB', Cmd.SETMINLB, int(val / 5 + 6), address=address))

    def set_max_voltage_logic_battery(self, val, address=None):
        """Sets logic input (LB- / LB+) maximum voltage level. RoboClaw will shutdown with an error if the voltage is above this level.

        :param float val: The valid data range is [6, 34].

        .. note:: This command is included for backwards compatibility. We recommend you use `set_main_voltages()` instead.
        """
        # translated byte value ranges [30, 175]
        # The formula for calculating the voltage is: Desired Volts x 5.12 = Value.
        # Examples of valid values are 12V = 62, 16V = 82 and 24V = 123.
        return self._send(pack('>BB', Cmd.SETMAXLB, int(val / 5.12), address=address))

    def set_m1_velocity_pid(self, p, i, d, qpps, address=None):
        """Several motor and quadrature combinations can be used with RoboClaw. In some cases the default PID values will need to be tuned for the systems being driven. This gives greater flexibility in what motor and encoder combinations can be used. The RoboClaw PID system consist of four constants starting with QPPS, P = Proportional, I= Integral and D= Derivative.

        :param int p: The default P is 0x00010000.
        :param int i: The default I is 0x00008000.
        :param int d: The default D is 0x00004000.
        :param int qpps: The default QPPS is 44000.

        QPPS is the speed of the encoder when the motor is at 100% power. P, I, D are the default values used after a reset.
        """
        # :Sends: [Address, 28, D(4 bytes), P(4 bytes), I(4 bytes), QPPS(4 byte)]
        return self._send(pack('>BIIII', Cmd.SETM1PID, d * 65536, p * 65536, i * 65536, qpps), address=address)

    def set_m2_velocity_pid(self, p, i, d, qpps, address=None):
        """Several motor and quadrature combinations can be used with RoboClaw. In some cases the default PID values will need to be tuned for the systems being driven. This gives greater flexibility in what motor and encoder combinations can be used. The RoboClaw PID system consist of four constants starting with QPPS, P = Proportional, I= Integral and D= Derivative.

        :param int p: The default P is 0x00010000.
        :param int i: The default I is 0x00008000.
        :param int d: The default D is 0x00004000.
        :param int qpps: The default QPPS is 44000.

        QPPS is the speed of the encoder when the motor is at 100% power. P, I, D are the default values used after a reset.
        """
        # :Sends: [Address, 29, D(4 bytes), P(4 bytes), I(4 bytes), QPPS(4 byte)]
        return self._send(pack('>BIIII', Cmd.SETM2PID, d * 65536, p * 65536, i * 65536, qpps), address=address)

    def read_raw_speed_m1(self, address=None):
        """Read the pulses counted in that last 300th of a second. This is an unfiltered version of `read_speed_m1()`. This function can be used to make a independent PID routine. Value returned is in encoder counts per second.

        :Returns: [Speed(4 bytes), Status]

        The Status byte is direction (0 – forward, 1 - backward).
        """
        return unpack('>Ib', _recv(self._send(pack('>B', Cmd.GETM1ISPEED), address=address, ack=5)))

    def read_raw_speed_m2(self, address=None):
        """Read the pulses counted in that last 300th of a second. This is an unfiltered version of `read_speed_m2()`. This function can be used to make a independent PID routine. Value returned is in encoder counts per second.

        :Returns: [Speed(4 bytes), Status]

        The Status byte is direction (0 – forward, 1 - backward).
        """
        return unpack('>Ib', _recv(self._send(pack('>B', Cmd.GETM2ISPEED), address=address, ack=5)))

    def duty_m1(self, val, address=None):
        """Drive M1 using a duty cycle value. The duty cycle is used to control the speed of the motor without a quadrature encoder.

        :param int val: The duty value is signed and the range [-32767, 32767] (eg. +-100% duty).
        """
        # :Sends: [Address, 32, Duty(2 Bytes)]
        return self._send(pack('>Bh', Cmd.M1DUTY, val), address=address)

    def duty_m2(self, val, address=None):
        """Drive M2 using a duty cycle value. The duty cycle is used to control the speed of the motor without a quadrature encoder.

        :param int val: The duty value is signed and the range [-32767, 32767] (eg. +-100% duty).
        """
        # :Sends: [Address, 33, Duty(2 Bytes)]
        return self._send(pack('>Bh', Cmd.M2DUTY, val), address=address)

    def duty_m1_m2(self, m1, m2, address=None):
        """Drive both M1 and M2 using a duty cycle value. The duty cycle is used to control the speed of the motor without a quadrature encoder.

        :param int m1: The duty value is signed and the range [-32767, 32767] (eg. +-100% duty).
        :param int m2: The duty value is signed and the range [-32767, 32767] (eg. +-100% duty).
        """
        # :Sends: [Address, 34, DutyM1(2 Bytes), DutyM2(2 Bytes)]
        return self._send(pack('>Bhh', Cmd.MIXEDDUTY, m1, m2), address=address)

    def speed_m1(self, val, address=None):
        """Drive M1 using a speed value. The sign indicates which direction the motor will turn. This command is used to drive the motor by quad pulses per second. Different quadrature encoders will have different rates at which they generate the incoming pulses. The values used will differ from one encoder to another. Once a value is sent the motor will begin to accelerate as fast as possible until the defined rate is reached.

        :param int val: Valid input ranges [-2147483647, 2147483647].
        """
        # :Sends: [Address, 35, Speed(4 Bytes)]
        return self._send(pack('>Bi', Cmd.M1SPEED, val), address=address)

    def speed_m2(self, val, address=None):
        """Drive M2 with a speed value. The sign indicates which direction the motor will turn. This command is used to drive the motor by quad pulses per second. Different quadrature encoders will have different rates at which they generate the incoming pulses. The values used will differ from one encoder to another. Once a value is sent, the motor will begin to accelerate as fast as possible until the rate defined is reached.

        :param int val: Valid input ranges [-2147483647, 2147483647].
        """
        # :Sends: [Address, 36, Speed(4 Bytes)]
        return self._send(pack('>Bi', Cmd.M2SPEED, val), address=address)

    def speed_m1_m2(self, m1, m2, address=None):
        """Drive M1 and M2 in the same command using a signed speed value. The sign indicates which direction the motor will turn. This command is used to drive the motor by quad pulses per second. Different quadrature encoders will have different rates at which they generate the incoming pulses. The values used will differ from one encoder to another. Once a value is sent the motor will begin to accelerate as fast as possible until the rate defined is reached.

        :param int m1: Valid input ranges [-2147483647, 2147483647].
        :param int m2: Valid input ranges [-2147483647, 2147483647].
        """
        # :Sends: [Address, 37, SpeedM1(4 Bytes), SpeedM2(4 Bytes)]
        return self._send(pack('>Bii', Cmd.MIXEDSPEED, m1, m2), address=address)

    def speed_accel_m1(self, accel, speed, address=None):
        """Drive M1 with a signed speed and acceleration value. The sign indicates which direction the motor will run. The acceleration values are not signed. This command is used to drive the motor by quad pulses per second and using an acceleration value for ramping. Different quadrature encoders will have different rates at which they generate the incoming pulses. The values used will differ from one encoder to another. Once a value is sent the motor will begin to accelerate incrementally until the rate defined is reached.

        The acceleration is measured in speed increase per second. An acceleration value of 12,000 QPPS with a speed of 12,000 QPPS would accelerate a motor from 0 to 12,000 QPPS in 1 second. Another example would be an acceleration value of 24,000 QPPS and a speed value of 12,000 QPPS would accelerate the motor to 12,000 QPPS in 0.5 seconds.
        """
        # :Sends: [Address, 38, Accel(4 Bytes), Speed(4 Bytes)]
        return self._send(pack('>BIi', Cmd.M1SPEEDACCEL, accel, speed), address=address)

    def speed_accel_m2(self, accel, speed, address=None):
        """Drive M2 with a signed speed and acceleration value. The sign indicates which direction the motor will run. The acceleration value is not signed. This command is used to drive the motor by quad pulses per second and using an acceleration value for ramping. Different quadrature encoders will have different rates at which they generate the incoming pulses. The values used will differ from one encoder to another. Once a value is sent the motor will begin to accelerate incrementally until the rate defined is reached.

        The acceleration is measured in speed increase per second. An acceleration value of 12,000 QPPS with a speed of 12,000 QPPS would accelerate a motor from 0 to 12,000 QPPS in 1 second. Another example would be an acceleration value of 24,000 QPPS and a speed value of 12,000 QPPS would accelerate the motor to 12,000 QPPS in 0.5 seconds.
        """
        # :Sends: [Address, 39, Accel(4 Bytes), Speed(4 Bytes)]
        return self._send(pack('>BIi', Cmd.M2SPEEDACCEL, accel, speed), address=address)

    def speed_accel_m1_m2(self, accel, speed1, speed2, address=None):
        """Drive M1 and M2 in the same command using one value for acceleration and two signed speed values for each motor. The sign indicates which direction the motor will run. The acceleration value is not signed. The motors are sync during acceleration. This command is used to drive the motor by quad pulses per second and using an acceleration value for ramping. Different quadrature encoders will have different rates at which they generate the incoming pulses. The values used will differ from one encoder to another. Once a value is sent the motor will begin to accelerate incrementally until the rate defined is reached.

        The acceleration is measured in speed increase per second. An acceleration value of 12,000 QPPS with a speed of 12,000 QPPS would accelerate a motor from 0 to 12,000 QPPS in 1 second. Another example would be an acceleration value of 24,000 QPPS and a speed value of 12,000 QPPS would accelerate the motor to 12,000 QPPS in 0.5 seconds.
        """
        # :Sends: [Address, 40, Accel(4 Bytes), SpeedM1(4 Bytes), SpeedM2(4 Bytes)]
        return self._send(pack('>BIii', Cmd.MIXEDSPEEDACCEL, accel, speed1, speed2), address=address)

    def speed_distance_m1(self, speed, distance, buffer, address=None):
        """Drive M1 with a signed speed and distance value. The sign indicates which direction the motor will run. The distance value is not signed. This command is buffered. This command is used to control the top speed and total distance traveled by the motor. Each motor channel M1 and M2 have separate buffers. This command will execute immediately if no other command for that channel is executing, otherwise the command will be buffered in the order it was sent. Any buffered or executing command can be stopped when a new command is issued by setting the Buffer argument. All values used are in quad pulses per second.

        The Buffer argument can be set to a 1 or 0. If a value of 0 is used the command will be buffered and executed in the order sent. If a value of 1 is used the current running command is stopped, any other commands in the buffer are deleted and the new command is executed.
        """
        # :Sends: [Address, 41, Speed(4 Bytes), Distance(4 Bytes), Buffer]
        return self._send(pack('>BiIB', Cmd.M1SPEEDDIST, speed, distance, buffer), address=address)

    def speed_distance_m2(self, speed, distance, buffer, address=None):
        """Drive M2 with a speed and distance value. The sign indicates which direction the motor will run. The distance value is not signed. This command is buffered. Each motor channel M1 and M2 have separate buffers. This command will execute immediately if no other command for that channel is executing, otherwise the command will be buffered in the order it was sent. Any buffered or executing command can be stopped when a new command is issued by setting the Buffer argument. All values used are in quad pulses per second.

        The Buffer argument can be set to a 1 or 0. If a value of 0 is used the command will be buffered and executed in the order sent. If a value of 1 is used the current running command is stopped, any other commands in the buffer are deleted and the new command is executed.
        """
        # :Sends: [Address, 42, Speed(4 Bytes), Distance(4 Bytes), Buffer]
        return self._send(pack('>BiIB', Cmd.M2SPEEDDIST, speed, distance, buffer), address=address)

    def speed_distance_m1_m2(self, speed1, distance1, speed2, distance2, buffer, address=None):
        """Drive M1 and M2 with a speed and distance value. The sign indicates which direction the motor will run. The distance value is not signed. This command is buffered. Each motor channel M1 and M2 have separate buffers. This command will execute immediately if no other command for that channel is executing, otherwise the command will be buffered in the order it was sent. Any buffered or executing command can be stopped when a new command is issued by setting the Buffer argument. All values used are in quad pulses per second.

        The Buffer argument can be set to a 1 or 0. If a value of 0 is used the command will be buffered and executed in the order sent. If a value of 1 is used the current running command is stopped, any other commands in the buffer are deleted and the new command is executed.
        """
        # :Sends: [Address, 43, SpeedM1(4 Bytes), DistanceM1(4 Bytes), SpeedM2(4 Bytes), DistanceM2(4 Bytes), Buffer]
        return self._send(pack('>BiIiIB', Cmd.MIXEDSPEEDDIST, speed1, distance1, speed2, distance2, buffer), address=address)

    def speed_accel_distance_m1(self, accel, speed, distance, buffer, address=None):
        """Drive M1 with a speed, acceleration and distance value. The sign indicates which direction the motor will run. The acceleration and distance values are not signed. This command is used to control the motors top speed, total distanced traveled and at what incremental acceleration value to use until the top speed is reached. Each motor channel M1 and M2 have separate buffers. This command will execute immediately if no other command for that channel is executing, otherwise the command will be buffered in the order it was sent. Any buffered or executing command can be stopped when a new command is issued by setting the Buffer argument. All values used are in quad pulses per second.

        The Buffer argument can be set to a 1 or 0. If a value of 0 is used the command will be buffered and executed in the order sent. If a value of 1 is used the current running command is stopped, any other commands in the buffer are deleted and the new command is executed.
        """
        # :Sends: [Address, 44, Accel(4 bytes), Speed(4 Bytes), Distance(4 Bytes), Buffer]
        return self._send(pack('>BIiIB', Cmd.M1SPEEDACCELDIST, accel, speed, distance, buffer), address=address)

    def speed_accel_distance_m2(self, accel, speed, distance, buffer, address=None):
        """Drive M2 with a speed, acceleration and distance value. The sign indicates which direction the motor will run. The acceleration and distance values are not signed. This command is used to control the motors top speed, total distanced traveled and at what incremental acceleration value to use until the top speed is reached. Each motor channel M1 and M2 have separate buffers. This command will execute immediately if no other command for that channel is executing, otherwise the command will be buffered in the order it was sent. Any buffered or executing command can be stopped when a new command is issued by setting the Buffer argument. All values used are in quad pulses per second.

        The Buffer argument can be set to a 1 or 0. If a value of 0 is used the command will be buffered and executed in the order sent. If a value of 1 is used the current running command is stopped, any other commands in the buffer are deleted and the new command is executed.
        """
        # :Sends: [Address, 45, Accel(4 bytes), Speed(4 Bytes), Distance(4 Bytes), Buffer]
        return self._send(pack('>BIiIB', Cmd.M2SPEEDACCELDIST, accel, speed, distance, buffer), address=address)

    def speed_accel_distance_m1_m2(self, accel, speed1, distance1, speed2, distance2, buffer, address=None):
        """Drive M1 and M2 with a speed, acceleration and distance value. The sign indicates which direction the motor will run. The acceleration and distance values are not signed. This command is used to control both motors top speed, total distanced traveled and at what incremental acceleration value to use until the top speed is reached. Each motor channel M1 and M2 have separate buffers. This command will execute immediately if no other command for that channel is executing, otherwise the command will be buffered in the order it was sent. Any buffered or executing command can be stopped when a new command is issued by setting the Buffer argument. All values used are in quad pulses per second.

        The Buffer argument can be set to a 1 or 0. If a value of 0 is used the command will be buffered and executed in the order sent. If a value of 1 is used the current running command is stopped, any other commands in the buffer are deleted and the new command is executed.
        """
        # :Sends: [Address, 46, Accel(4 Bytes), SpeedM1(4 Bytes), DistanceM1(4 Bytes), SpeedM2(4 bytes), DistanceM2(4 Bytes), Buffer]
        return self._send(pack('>BIiIiIB', Cmd.MIXEDSPEEDACCELDIST, accel, speed1, distance1, speed2, distance2, buffer), address=address)

    def read_buffer_length(self, address=None):
        """Read both motor M1 and M2 buffer lengths. This command can be used to determine how many commands are waiting to execute.

        :Returns: [BufferM1, BufferM2]

        The return values represent how many commands per buffer are waiting to be executed. The maximum buffer size per motor is 64 commands(0x3F). A return value of 0x80(128) indicates the buffer is empty. A return value of 0 indiciates the last command sent is executing. A value of 0x80 indicates the last command buffered has finished.
        """
        val = unpack('>BB', _recv(self._send(pack('>B', Cmd.GETBUFFERS), address=address, ack=2)))
        if val:
            return (1, val[0], val[1])
        return (0, 0, 0)

    def read_pwms(self, address=None):
        """Read the current PWM output values for the motor channels. The values returned are +/-32767. The duty cycle percent is calculated by dividing the Value by 327.67.

        :Returns: [M1 PWM(2 bytes), M2 PWM(2 bytes)]
        """
        # Send: [Address, 48]
        val = unpack('>hh', _recv(self._send(pack('>B', Cmd.GETPWMS), address=address, ack=4)))
        if val:
            return (1, val[0], val[1])
        return (0, 0, 0)

    def read_currents(self, address=None):
        """Read the current draw from each motor in 10ma increments. The amps value is calculated by dividing the value by 100.

        :Returns: [M1 Current(2 bytes), M2 Currrent(2 bytes)]
        """
        # Send: [Address, 49]
        val = unpack('>hh', _recv(self._send(pack('>B', Cmd.GETCURRENTS), address=address, ack=4)))
        if val:
            return (1, val[0], val[1])
        return (0, 0, 0)

    def speed_accel_m1_m2_2(self, accel1, speed1, accel2, speed2, address=None):
        """Drive M1 and M2 in the same command using one value for acceleration and two signed speed values for each motor. The sign indicates which direction the motor will run. The acceleration value is not signed. The motors are sync during acceleration. This command is used to drive the motor by quad pulses per second and using an acceleration value for ramping. Different quadrature encoders will have different rates at which they generate the incoming pulses. The values used will differ from one encoder to another. Once a value is sent the motor will begin to accelerate incrementally until the rate defined is reached.

        The acceleration is measured in speed increase per second. An acceleration value of 12,000 QPPS with a speed of 12,000 QPPS would accelerate a motor from 0 to 12,000 QPPS in 1 second. Another example would be an acceleration value of 24,000 QPPS and a speed value of 12,000 QPPS would accelerate the motor to 12,000 QPPS in 0.5 seconds.
        """
        # :Sends: [Address, 50, AccelM1(4 Bytes), SpeedM1(4 Bytes), AccelM2(4 Bytes), SpeedM2(4 Bytes)]
        return self._send(pack('>BIiIi', Cmd.MIXEDSPEED2ACCEL, accel1, speed1, accel2, speed2), address=address)

    def speed_accel_distance_m1_m2_2(self, accel1, speed1, distance1, accel2, speed2, distance2, buffer, address=None):
        """Drive M1 and M2 in the same command using one value for acceleration and two signed speed values for each motor. The sign indicates which direction the motor will run. The acceleration value is not signed. The motors are sync during acceleration. This command is used to drive the motor by quad pulses per second and using an acceleration value for ramping. Different quadrature encoders will have different rates at which they generate the incoming pulses. The values used will differ from one encoder to another. Once a value is sent the motor will begin to accelerate incrementally until the rate defined is reached.

        The acceleration is measured in speed increase per second. An acceleration value of 12,000 QPPS with a speed of 12,000 QPPS would accelerate a motor from 0 to 12,000 QPPS in 1 second. Another example would be an acceleration value of 24,000 QPPS and a speed value of 12,000 QPPS would accelerate the motor to 12,000 QPPS in 0.5 seconds.
        """
        # :Sends: [Address, 50, AccelM1(4 Bytes), SpeedM1(4 Bytes), AccelM2(4 Bytes), SpeedM2(4 Bytes)]
        return self._send(pack('>BIiIIiIB', Cmd.MIXEDSPEED2ACCELDIST, accel1, speed1, distance1, accel2, speed2, distance2, buffer), address=address)

    def duty_accel_m1(self, accel, duty, address=None):
        """Drive M1 with a signed duty and acceleration value. The sign indicates which direction the motor will run. The acceleration values are not signed. This command is used to drive the motor by PWM and using an acceleration value for ramping. Accel is the rate per second at which the duty changes from the current duty to the specified duty.

        The duty value is signed and the range is -32768 to +32767(eg. +-100% duty). The accel value range is 0 to 655359(eg maximum acceleration rate is -100% to 100% in 100ms).
        """
        # :Sends: [Address, 52, Duty(2 bytes), Accel(2 Bytes)]
        return self._send(pack('>BhI', Cmd.M1DUTYACCEL, duty, accel), address=address)

    def duty_accel_m2(self, accel, duty, address=None):
        """Drive M2 with a signed duty and acceleration value. The sign indicates which direction the motor will run. The acceleration values are not signed. This command is used to drive the motor by PWM and using an acceleration value for ramping. Accel is the rate at which the duty changes from the current duty to the specified dury.

        The duty value is signed and the range is -32768 to +32767 (eg. +-100% duty). The accel value range is 0 to 655359 (eg maximum acceleration rate is -100% to 100% in 100ms).
        """
        # :Sends: [Address, 53, Duty(2 bytes), Accel(2 Bytes)]
        return self._send(pack('>BhI', Cmd.M2DUTYACCEL, duty, accel), address=address)

    def duty_accel_m1_m2(self, accel1, duty1, accel2, duty2, address=None):
        """Drive M1 and M2 in the same command using acceleration and duty values for each motor. The sign indicates which direction the motor will run. The acceleration value is not signed. This command is used to drive the motor by PWM using an acceleration value for ramping.

        The duty value is signed and the range is -32768 to +32767 (eg. +-100% duty). The accel value range is 0 to 655359 (eg maximum acceleration rate is -100% to 100% in 100ms).
        """
        # :Sends: [Address, CMD, DutyM1(2 bytes), AccelM1(4 Bytes), DutyM2(2 bytes), AccelM1(4 bytes)]
        return self._send(pack('>BhIhI', Cmd.MIXEDDUTYACCEL, duty1, accel1, duty2, accel2), address=address)

    def read_m1_velocity_pid(self, address=None):
        """Read the PID and QPPS Settings.

        :Returns: [P(4 bytes), I(4 bytes), D(4 bytes), QPPS(4 byte)]
        """
        # :Sends: [Address, 55]
        data = unpack('iiii', _recv(self._send(pack('>B', Cmd.READM1PID), address=address, ack=16)))
        if data:
            return (data[0], data[1] / 65536.0, data[2] / 65536.0, data[3] / 65536.0)
        return (0, 0, 0, 0)

    def read_m2_velocity_pid(self, address=None):
        """Read the PID and QPPS Settings.

        :Returns: [P(4 bytes), I(4 bytes), D(4 bytes), QPPS(4 byte)]
        """
        # :Sends: [Address, 55]
        data = unpack('iiii', _recv(self._send(pack('>B', Cmd.READM2PID), address=address, ack=16)))
        if data:
            return (data[0], data[1] / 65536.0, data[2] / 65536.0, data[3] / 65536.0)
        return (0, 0, 0, 0)

    def set_main_voltages(self, minimum, maximum, address=None):
        """Set the Main Battery Voltage cutoffs, Min and Max. Min and Max voltages are in 10th of a volt increments. Multiply the voltage to set by 10."""
        # :Sends: [Address, 57, Min(2 bytes), Max(2bytes]
        return self._send(pack('>BHH', Cmd.SETMAINVOLTAGES, minimum, maximum), address=address)

    def set_logic_voltages(self, minimum, maximum, address=None):
        """Set the Logic Battery Voltages cutoffs, Min and Max. Min and Max voltages are in 10th of a volt increments. Multiply the voltage to set by 10."""
        # :Sends: [Address, 58, Min(2 bytes), Max(2bytes]
        return self._send(pack('>BHH', Cmd.SETLOGICVOLTAGES, minimum, maximum), address=address)

    def read_min_max_main_voltages(self, address=None):
        """Read the Main Battery Voltage Settings. The voltage is calculated by dividing the value by 10

        :Returns: [Min(2 bytes), Max(2 bytes)]
        """
        val = unpack('>HH', _recv(self._send(pack('>B', Cmd.GETMINMAXMAINVOLTAGES), address=address, ack=4)))
        if val:
            return (1, val[0], val[1])
        return (0, 0, 0)

    def read_min_max_logic_voltages(self, address=None):
        """Read the Logic Battery Voltage Settings. The voltage is calculated by dividing the value by 10

        :Returns: [Min(2 bytes), Max(2 bytes)]
        """
        val = unpack('>HH', _recv(self._send(pack('>B', Cmd.GETMINMAXLOGICVOLTAGES), address=address, ack=4)))
        if val:
            return (1, val[0], val[1])
        return (0, 0, 0)

    def set_m1_position_pid(self, kp, ki, kd, kimax, deadzone, minimum, maximum, address=None):
        """The RoboClaw Position PID system consist of seven constants starting with P = Proportional, I= Integral and D= Derivative, MaxI = Maximum Integral windup, Deadzone in encoder counts, MinPos = Minimum Position and MaxPos = Maximum Position. The defaults values are all zero.

        Position constants are used only with the Position commands, 65,66 and 67 or when encoders are enabled in RC/Analog modes.
        """
        # :Sends: [Address, 61, D(4 bytes), P(4 bytes), I(4 bytes), MaxI(4 bytes), Deadzone(4 bytes), MinPos(4 bytes), MaxPos(4 bytes)]
        return self._send(pack('>BIIIIIII', Cmd.SETM1POSPID, kd * 1024, kp * 1024, ki * 1024, kimax, deadzone, minimum, maximum), address=address)

    def set_m2_position_pid(self, kp, ki, kd, kimax, deadzone, minimum, maximum, address=None):
        """The RoboClaw Position PID system consist of seven constants starting with P = Proportional, I= Integral and D= Derivative, MaxI = Maximum Integral windup, Deadzone in encoder counts, MinPos = Minimum Position and MaxPos = Maximum Position. The defaults values are all zero.

        Position constants are used only with the Position commands, 65,66 and 67 or when encoders are enabled in RC/Analog modes.
        """
        # :Sends: [Address, 62, D(4 bytes), P(4 bytes), I(4 bytes), MaxI(4 bytes), Deadzone(4 bytes), MinPos(4 bytes), MaxPos(4 bytes)]
        return self._send(pack('>BIIIIIII', Cmd.SETM2POSPID, kd * 1024, kp * 1024, ki * 1024, kimax, deadzone, minimum, maximum), address=address)

    def read_m1_position_pid(self, address=None):
        """Read the Position PID Settings.

        :Returns: [P(4 bytes), I(4 bytes), D(4 bytes), MaxI(4 byte), Deadzone(4 byte), MinPos(4 byte), MaxPos(4 byte)]
        """
        data = unpack('>IIIIIII', _recv(self._send(pack('>B', Cmd.READM1POSPID), address=address, ack=28)))
        if data:
            return (data[0], data[1] / 1024.0, data[2] / 1024.0, data[3] / 1024.0)
        return (0, 0, 0, 0, 0, 0, 0)

    def read_m2_position_pid(self, address=None):
        """Read the Position PID Settings.

        :Returns: [P(4 bytes), I(4 bytes), D(4 bytes), MaxI(4 byte), Deadzone(4 byte), MinPos(4 byte), MaxPos(4 byte)]
        """
        data = unpack('>IIIIIII', _recv(self._send(pack('>B', Cmd.READM2POSPID), address=address, ack=28)))
        if data:
            return (1, data[0] / 1024.0, data[1] / 1024.0, data[2] / 1024.0)
        return (0, 0, 0, 0, 0, 0, 0)

    def speed_accel_deccel_position_m1(self, accel, speed, deccel, position, buffer, address=None):
        """Move M1 position from the current position to the specified new position and hold the new position. Accel sets the acceleration value and deccel the decceleration value. QSpeed sets the speed in quadrature pulses the motor will run at after acceleration and before decceleration.
        """
        # :Sends: [Address, 65, Accel(4 bytes), Speed(4 Bytes), Deccel(4 bytes), Position(4 Bytes), Buffer]
        return self._send(pack('>BIIIIB', Cmd.M1SPEEDACCELDECCELPOS, accel, speed, deccel, position, buffer), address=address)

    def speed_accel_deccel_position_m2(self, accel, speed, deccel, position, buffer, address=None):
        """Move M2 position from the current position to the specified new position and hold the new position. Accel sets the acceleration value and deccel the decceleration value. QSpeed sets the speed in quadrature pulses the motor will run at after acceleration and before decceleration.
        """
        # :Sends: [Address, 66, Accel(4 bytes), Speed(4 Bytes), Deccel(4 bytes), Position(4 Bytes), Buffer]
        return self._send(pack('>BIIIIB', Cmd.M2SPEEDACCELDECCELPOS, accel, speed, deccel, position, buffer), address=address)

    def speed_accel_deccel_position_m1_m2(self, accel1, speed1, deccel1, position1, accel2, speed2, deccel2, position2, buffer, address=None):
        """Move M1 & M2 positions from their current positions to the specified new positions and hold the new positions. Accel sets the acceleration value and deccel the decceleration value. QSpeed sets the speed in quadrature pulses the motor will run at after acceleration and before decceleration.
        """
        # :Sends: [Address, 67, AccelM1(4 bytes), SpeedM1(4 Bytes), DeccelM1(4 bytes), PositionM1(4 Bytes), AccelM2(4 bytes), SpeedM2(4 Bytes), DeccelM2(4 bytes), PositionM2(4 Bytes), Buffer]
        return self._send(pack('>BIIIIIIIIB', Cmd.MIXEDSPEEDACCELDECCELPOS, accel1, speed1, deccel1, position1, accel2, speed2, deccel2, position2, buffer), address=address)

    def set_m1_default_accel(self, accel, address=None):
        """Set the default acceleration for M1 when using duty cycle commands (`duty_m1()` and `duty_m1_m2()`) or when using Standard Serial, RC and Analog PWM modes.
        """
        # :Sends: [Address, 68, Accel(4 bytes)]
        return self._send(pack('>BI', Cmd.SETM1DEFAULTACCEL, accel), address=address)

    def set_m2_default_accel(self, accel, address=None):
        """Set the default acceleration for M2 when using duty cycle commands (`duty_m2()` and `duty_m1_m2()`) or when using Standard Serial, RC and Analog PWM modes.
        """
        # :Sends: [Address, 69, Accel(4 bytes)]
        return self._send(pack('>BI', Cmd.SETM2DEFAULTACCEL, accel), address=address)

    def set_pin_functions(self, s3mode, s4mode, s5mode, address=None):
        """Set modes for S3,S4 and S5.

        ==== ================ ================ ================
        Mode S3mode           S4mode           S5mode
        ==== ================ ================ ================
        0    Default          Disabled         Disabled
        1    E-Stop(latching) E-Stop(latching) E-Stop(latching)
        2    E-Stop           E-Stop           E-Stop
        3    Voltage Clamp    Voltage Clamp    Voltage Clamp
        4                     M1 Home          M2 Home
        ==== ================ ================ ================

        Mode Description
            - Disabled: pin is inactive.
            - Default: Flip switch if in RC/Analog mode or E-Stop(latching) in Serial modes.
            - E-Stop(Latching): causes the Roboclaw to shutdown until the unit is power cycled.
            - E-Stop: Holds the Roboclaw in shutdown until the E-Stop signal is cleared.
            - Voltage Clamp: Sets the signal pin as an output to drive an external voltage clamp circuit.
            - Home(M1 & M2): will trigger the specific motor to stop and the encoder count to reset to 0.
        """
        # :Returns: [0xFF]
        # :Sends: [Address, 74, S3mode, S4mode, S5mode]
        return self._send(pack('>BBBB', Cmd.SETPINFUNCTIONS, s3mode, s4mode, s5mode), address=address)

    def read_pin_functions(self, address=None):
        """Read mode settings for S3,S4 and S5. See `set_pin_functions()` for mode descriptions

        :Returns: [S3mode, S4mode, S5mode]
        """
        # :Sends: [Address, 75]
        val = unpack('>BBB', _recv(self._send(pack('>B', Cmd.GETPINFUNCTIONS), address=address, ack=3)))
        if val:
            return (1, val[0], val[1], val[2])
        return (0, 0, 0)

    def set_deadband(self, minimum, maximum, address=None):
        """Set RC/Analog mode control deadband percentage in 10ths of a percent. Default value is 25(2.5%). Minimum value is 0(no DeadBand), Maximum value is 250(25%).
        """
        # :Sends: [Address, 76, Reverse, Forward]
        # :Returns: [0xFF]
        return self._send(pack('>BBB', Cmd.SETDEADBAND, minimum, maximum), address=address)

    def get_deadband(self, address=None):
        """Read DeadBand settings in 10ths of a percent.

        :Returns: [Reverse, SForward]
        """
        # :Sends: [Address, 77]
        val = unpack('>BB', _recv(self._send(pack('>B', Cmd.GETDEADBAND), address=address, ack=2)))
        if val:
            return (1, val[0], val[1])
        return (0, 0, 0)

    def restore_defaults(self, address=None):
        """Reset Settings to factory defaults.

        .. warning::Concerning TTL Serial:
            Baudrate will change if not already set to 38400.  Communications will be lost.
        """
        # :Sends: [Address, 80]
        return self._send(pack('>B', Cmd.RESTOREDEFAULTS), address=address)

    def read_temp(self, address=None):
        """Read the board temperature. Value returned is in 10ths of degrees.

        :Returns: [Temperature(2 bytes)]
        """
        return unpack('>h', _recv(self._send(pack('>B', Cmd.GETTEMP), address=address, ack=2)))

    def read_temp2(self, address=None):
        """Read the second board temperature(only on supported units). Value returned is in 10ths of degrees.

        :Returns: [Temperature(2 bytes)]
        """
        return unpack('>h', _recv(self._send(pack('>B', Cmd.GETTEMP2), address=address, ack=2)))

    def read_error(self, address=None):
        """Read the current unit status.

        :Returns: [Status]

        ========================= ===============
        Function                  Status Bit Mask
        ========================= ===============
        Normal                    0x0000
        M1 OverCurrent Warning    0x0001
        M2 OverCurrent Warning    0x0002
        E-Stop                    0x0004
        Temperature Error         0x0008
        Temperature2 Error        0x0010
        Main Battery High Error   0x0020
        Logic Battery High Error  0x0040
        Logic Battery Low Error   0x0080
        Main Battery High Warning 0x0400
        Main Battery Low Warning  0x0800
        Termperature Warning      0x1000
        Temperature2 Warning      0x2000
        ========================= ===============
        """
        return unpack('>B', _recv(self._send(pack('>B', Cmd.GETERROR), address=address, ack=1)))

    def read_encoder_modes(self, address=None):
        """Read the encoder pins assigned for both motors.

        :Returns: [Enc1Mode, Enc2Mode]
        """
        val = unpack('>BB', _recv(self._send(pack('>B', Cmd.GETENCODERMODE), address=address, ack=2)))
        if val:
            return (1, val[0], val[1])
        return (0, 0, 0)

    def set_m1_encoder_mode(self, mode, address=None):
        """Set the Encoder Pin for motor 1. See `read_encoder_modes()`."""
        # :Sends: [Address, 92, Pin]
        return self._send(pack('>BB', Cmd.SETM1ENCODERMODE, mode), address=address)

    def set_m2_encoder_mode(self, mode, address=None):
        """Set the Encoder Pin for motor 2. See `read_encoder_modes()`."""
        # :Sends: [Address, 93, Pin]
        return self._send(pack('>BB', Cmd.SETM2ENCODERMODE, mode), address=address)

    def write_nvm(self, address=None):
        """Writes all settings to non-volatile memory. Values will be loaded after each power up.
        """
        # :Sends: [Address, 94]
        return self._send(pack('>BI', Cmd.WRITENVM, 0xE22EAB7A), address=address)

    def read_nvm(self, address=None):
        """Read all settings from non-volatile memory.

        :Returns: [Enc1Mode, Enc2Mode]

        .. warning:: Concerning TTL Serial:
            If baudrate changes or the control mode changes communications will be lost.
        """
        # :Sends: [Address, 95]
        return unpack('>BB', _recv(self._send(pack('>B', Cmd.READNVM), address=address, ack=2)))

    def set_config(self, config, address=None):
        """Set config bits for standard settings.

        =================== ===============
        Function            Config Bit Mask
        =================== ===============
        RC Mode             0x0000
        Analog Mode         0x0001
        Simple Serial Mode  0x0002
        Packet Serial Mode  0x0003
        Battery Mode Off    0x0000
        Battery Mode Auto   0x0004
        Battery Mode 2 Cell 0x0008
        Battery Mode 3 Cell 0x000C
        Battery Mode 4 Cell 0x0010
        Battery Mode 5 Cell 0x0014
        Battery Mode 6 Cell 0x0018
        Battery Mode 7 Cell 0x001C
        Mixing              0x0020
        Exponential         0x0040
        MCU                 0x0080
        BaudRate 2400       0x0000
        BaudRate 9600       0x0020
        BaudRate 19200      0x0040
        BaudRate 38400      0x0060
        BaudRate 57600      0x0080
        BaudRate 115200     0x00A0
        BaudRate 230400     0x00C0
        BaudRate 460800     0x00E0
        FlipSwitch          0x0100
        Packet Address 0x80 0x0000
        Packet Address 0x81 0x0100
        Packet Address 0x82 0x0200
        Packet Address 0x83 0x0300
        Packet Address 0x84 0x0400
        Packet Address 0x85 0x0500
        Packet Address 0x86 0x0600
        Packet Address 0x87 0x0700
        Slave Mode          0x0800
        Relay Mode          0x1000
        Swap Encoders       0x2000
        Swap Buttons        0x4000
        Multi-Unit Mode     0x8000
        =================== ===============

        .. warning:: Concerning TTL Serial:
            * If control mode is changed from packet serial mode when setting config communications will be lost!
            * If baudrate of packet serial mode is changed communications will be lost!
        """
        # :Sends: [Address, 98, Config(2 bytes)]
        # :Returns: [0xFF]
        return self._send(pack('>Bh', Cmd.SETCONFIG, config), address=address)

    def get_config(self, address=None):
        """Read config bits for standard settings See `set_config()`.

        :Returns: [Config(2 bytes)]
        """
        # :Sends: [Address, 99]
        return unpack('>h', _recv(self._send(pack('>B', Cmd.GETCONFIG), address=address, ack=2)))

    def set_m1_max_current(self, maximum, address=None):
        """Set Motor 1 Maximum Current Limit. Current value is in 10ma units. To calculate multiply current limit by 100.
        """
        # :Sends: [Address, 134, MaxCurrent(4 bytes), 0, 0, 0, 0]
        return self._send(pack('>BII', Cmd.SETM1MAXCURRENT, maximum, 0), address=address)

    def set_m2_max_current(self, maximum, address=None):
        """Set Motor 2 Maximum Current Limit. Current value is in 10ma units. To calculate multiply current limit by 100.
        """
        # :Sends: [Address, 134, MaxCurrent(4 bytes), 0, 0, 0, 0]
        return self._send(pack('>BII', Cmd.SETM2MAXCURRENT, maximum, 0), address=address)

    def read_m1_max_current(self, address=None):
        """Read Motor 1 Maximum Current Limit. Current value is in 10ma units. To calculate divide value by 100. MinCurrent is always 0.

        :Returns: [MaxCurrent(4 bytes), MinCurrent(4 bytes)]
        """
        data = unpack('>II', _recv(self._send(pack('>B', Cmd.GETM1MAXCURRENT), address=address, ack=8)))
        if data:
            return data
        return (0, 0)

    def read_m2_max_current(self, address=None):
        """Read Motor 2 Maximum Current Limit. Current value is in 10ma units. To calculate divide value by 100. MinCurrent is always 0.

        :Returns: [MaxCurrent(4 bytes), MinCurrent(4 bytes)]
        """
        data = unpack('>II', _recv(self._send(pack('>B', Cmd.GETM2MAXCURRENT), address=address, ack=8)))
        if data[0]:
            return data
        return (0, 0)

    def set_pwm_mode(self, mode, address=None):
        """Set PWM Drive mode. Locked Antiphase(0) or Sign Magnitude(1).
        """
        # :Sends: [Address, 148, Mode]
        return self._send(pack('>BB', Cmd.SETPWMMODE, mode), address=address)

    def read_pwm_mode(self, address=None):
        """Read PWM Drive mode. See `set_pwm_mode()`.

        :Returns: [PWMMode]
        """
        return unpack('>B', _recv(self._send(pack('>B', Cmd.GETPWMMODE), address=address, ack=1)))

    def read_eeprom(self, ee_address, address=None):
        """Read a value from the User EEProm memory(256 bytes).

        :Returns: [Value(2 bytes)]
        """
        # :Sends: [Address, 252, EEProm Address(byte)]
        val = unpack('>H', _recv(self._send(pack('>BB', Cmd.READEEPROM, ee_address), address=address, ack=2)))
        if val:
            return (1, val[0])
        return (0, 0)

    def write_eeprom(self, ee_address, ee_word, address=None):
        """Get Priority Levels.
        """
        # :Sends: [Address, 253, Address(byte), Value(2 bytes)]
        val = unpack('>B', _recv(self._send(pack('>BBH', Cmd.WRITEEEPROM, ee_address, ee_word), address=address, ack=1, crc=0)))
        if val[1] == 0xaa:
            return True
        return False
