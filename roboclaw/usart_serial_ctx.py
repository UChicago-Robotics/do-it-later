"""This module contains a wrapper class for MicroPython's machine.UART and
CircuitPython's busio.UART class to work as a drop-in replacement to
pySerial's serial.Serial` object with python's context manager."""
# pylint: disable=import-error,too-many-arguments
MICROPY = False
try:
    from busio import UART
except ImportError: # running on a MicroPython board
    from machine import UART
    MICROPY = True

class SerialUART(UART):
    """A wrapper class for MicroPython's machine.UART class to utilize python's context
    manager. This wrapper may be incomplete as it is specialized for use with this library
    only as a drop-in replacement for CircuitPython's `busio.UART` or PySerial's
    `~serial.Serial` module API.

    :param ~microcontroller.Pin tx_pin: The pin used for sending data.
    :param ~microcontroller.Pin rx_pin: The pin used for receiving data.
    :param int baudrate: The baudrate of the Serial port. Defaults to ``9600``.
    :param int bits: The number of bits per byte. Options are limited to ``8`` or ``9``.
        Defaults to ``8``.
    :param int parity: This parameter is optional. The parity controls how the bytes are
        handled with respect the raising or falling edge of the clock signal. Options are
        limited to ``None``, ``0`` (even), or ``1`` (odd). Defaults to ``None``.
    :param int stop: The number of stop bits to be used to signify the end of the buffer
        payload (kinda like the null character in a C-style string). Options are limited to
        ``1`` or ``2``. Defaults to ``1``.
    """
    def __init__(self, tx_pin=None, rx_pin=None, baudrate=9600, bits=8, parity=None, stop=1):
        if MICROPY:
            super(SerialUART, self).__init__(
                tx=tx_pin, rx=rx_pin, baudrate=baudrate, bits=bits, parity=parity, stop=stop
            )
        else:
            super(SerialUART, self).__init__(
                tx_pin, rx_pin, baudrate=baudrate, bits=bits, parity=parity, stop=stop
            )

    def __enter__(self):
        """Used to reinitialize serial port with the correct configuration ("enter"
        ``with`` block)"""
        if MICROPY:
            self.init(
                baudrate=self.baudrate,
                bits=self.bits,
                parity=self.parity,
                stop=self.stop,
                tx=self.tx_pin,
                rx=self.rx_pin)
            return self
        return super().__enter__()

    # pylint: disable=arguments-differ
    def __exit__(self, *exc):
        """Deinitialize the serial port ("exit" ``with`` block)"""
        if MICROPY:
            self.deinit()
            return False
        return super().__exit__(*exc)

    def in_waiting(self):
        """The number of bytes waiting to be read on the open Serial port."""
        return self.any()

    def close(self):
        """ deinitialize the port """
        self.deinit()

    def read_until(self, size=None):
        """return a `bytearray` of received data.

        :param int size: If left unspecified, returns everything in the buffer terminated
            with a ``\n`` or internal timeout occurs. If specified, then returns everything the
            buffer up to at most the ``size`` number of bytes or internal timeout occurs"""
        if size is None:
            return self.readline()
        return self.read(size)
