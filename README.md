# somfyrts

Enables the control of Somfy motors and controls through a Somfy Universal RTS Interface device.  The module can be run from the command line or the class can be incorporated into custom home automation software.

To use this module, you must have a Universal RTS Interface attached to an RS232 port and you must know the name of the port.  Up, Down, and Stop commands can be sent to one or more specified channels.

The implementation offers a execution of the commands on a background thread so that the command operations will not block the calling thread.  Somfy recommends a minimum of 1.5 seconds between commands to avoid interference when sending the radio commands so the implementation inserts delays between commands.  Sending an Up command to five channels requires 6 seconds so using a background thread can be useful when sending several commands at once.
