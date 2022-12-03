
.. If you created a package, create one automodule per module in the package.

.. If your library file(s) are nested in a directory (e.g. /adafruit_foo/foo.py)
.. use this format as the module name: "adafruit_foo.foo"

Roboclaw
=============

Roboclaw driver class
---------------------

.. automodule:: roboclaw.roboclaw
    :members:

Roboclaw serial commands
------------------------

.. automodule:: roboclaw.serial_commands
    :members:

Helpers
===========

CRC16 data manipulation
------------------------

.. automodule:: roboclaw.data_manip
    :members:

UART Serial with context manager For MicroPython
-------------------------------------------------

This module contains a wrapper class for MicroPython's :py:class:`~machine.UART` or
CircuitPython's :py:class:`~busio.UART` class to work as a drop-in replacement to
:py:class:`~serial.Serial` object.

.. note:: This helper class does not expose all the pySerial API. It's tailored to this library only. That said, to use this:

    .. code-block:: python

        from roboclaw.usart_serial_ctx import SerialUART as UART
        serial_bus = UART()
        with serial_bus:
            serial_bus.read_until() # readline() with timeout
            serial_bus.in_waiting() # how many bytes in the RX buffer
            serial_bus.close() # same as UART.deinit()
        # exit ``with`` also calls machine.UART.deinit()

.. .. automodule:: roboclaw.usart_serial_ctx
