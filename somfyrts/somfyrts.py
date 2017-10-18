#!/usr/bin/env python3
#
# Somfy Universal RTS Interface controller communication software.
#
# This file is encompasses all of the functionality for the package
# Copyright (C) 2017 Ralph Lipe <ralph@lipe.ws>
#
# SPDX-License-Identifier:    MIT
"""\
Send motor control commands for Somfy RTS devices through Somfy Universal RTS controller
"""
import argparse
import datetime
import threading
import time
import serial

from .serialstub import SerialStub

import logging
logger = logging.getLogger(__name__)


class SomfyRTS:
    """Sends commands via RS232 serial interface to a Somfy Universal RTS Interface device"""

    def __init__(self, port, interval=1.5, version=1, thread=False):
        """Opens the specified port and initializes the RTS interface object.

        Keyword arguments:
        port -- url for serial port to open
        version -- either 1 or 2 depending on model of Universal RTS Interface
        thread -- if True then up(), down(), and stop() return immediately and will be processed asynchronously"""

        self._last_command_time = datetime.datetime.min
        self._interval_timedelta = datetime.timedelta(seconds=interval)
        self._version = version

        # For testing purposes, the special value 'TEST' will cause the class to use the SerialStub class.
        self._ser = SerialStub() if port == SerialStub.TEST_PORT_NAME else serial.Serial(port)

        self._lock = threading.Lock()
        self._command_queue = []
        self._check_queue = threading.Event()
        self._closed = threading.Event()
        self._queue_is_empty = threading.Event()
        self._queue_is_empty.set()
        self._thread = None
        if thread:
            self._thread = threading.Thread(target=lambda: self._thread_process_queue())
            self._thread.start()

    def __enter__(self):
        """Performs no function.  Returns original SomfyRTS object (self)."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Closes the serial port and terminates the background thread if there is one."""
        self.close()

    def _thread_process_queue(self):
        while self._process_command_queue():
            self._check_queue.wait()

    # Returns True if all commands have been processed.  Returns False if the command queue no longer exists indicating
    # that the close() method has been called
    def _process_command_queue(self):
        self._lock.acquire()
        while (not self._closed.isSet()) and (len(self._command_queue) > 0):
            # now we do one of two things:  sleep or process the command.  If we sleep then we want to check
            # the status of the queue again because it could have changed through close() or clear_command_queue()
            time_since_last_cmd = (datetime.datetime.now() - self._last_command_time)
            sleep_time = (self._interval_timedelta - time_since_last_cmd).total_seconds()
            if sleep_time > 0.0:
                logger.info("sleeping {0} seconds between commands".format(sleep_time))
                self._lock.release()
                self._closed.wait(timeout=sleep_time)
                self._lock.acquire()
            else:
                cmd = self._command_queue.pop(0)
                logger.info("sending command: {0}".format(cmd))
                self._ser.write(bytes(cmd, "utf-8"))
                self._last_command_time = datetime.datetime.now()
        self._queue_is_empty.set()
        self._check_queue.clear()
        keep_running = not self._closed.isSet()
        self._lock.release()
        return keep_running

    # channels can be None (function does nothing), an integer, or a collection of integers
    def _do_command(self, command, channels):
        if channels is not None:
            if isinstance(channels, int):
                self._do_single_command(command, channels)
            else:
                for c in channels:
                    self._do_single_command(command, c)

    def _do_single_command(self, command, channel):
        assert channel >= 1
        assert (self._version == 1 and channel <= 5) or (self._version == 2 and channel <= 16)
        assert command in ('U', 'D', 'S')
        assert not self._closed.isSet()

        # TODO:  The documentation for version II controller does not show a terminating \r for commands.  Because
        # TODO:  the author does not have a version II controller, he is unable to verify if this is correct.
        # TODO:  If a future user finds the answer, please either correct this code by adding a trailing \r and
        # TODO:  correcting test_version_2() or if a trailing \r is not required, please remove these comments.
        cmd = "{0}{1}\r" if self._version == 1 else "01{1:02}{0}"
        cmd = cmd.format(command, channel)

        with self._lock:
            self._command_queue.append(cmd)
            self._queue_is_empty.clear()
            self._check_queue.set()

        if self._thread is None:
            self._process_command_queue()

    def up(self, channels):
        """Send an up command to one or more channels

        Keyword arguments:
        channels - can be None, a single integer, or a collection of integer channel values"""
        self._do_command("U", channels)

    def down(self, channels):
        """Send a down command to one or more channels

        Keyword arguments:
        channels - can be None, a single integer, or a collection of integer channel values"""
        self._do_command("D", channels)

    def stop(self, channels):
        """Send a stop command to one or more channels

        Keyword arguments:
        channels - can be None, a single integer, or a collection of integer channel values"""
        self._do_command("S", channels)

    def clear_command_queue(self):
        """Discard any pending commands."""
        assert not self._closed.isSet()
        with self._lock:
            # No need to clear _check_command_queue since process loop will clear it for us.  Avoid potential race
            self._command_queue = []
            self._queue_is_empty.set()

    def flush_command_queue(self, timeout=None):
        """Process any pending commands. returns True and does nothing for objects created with 'thread=False'.

        returns True if all commands are processed.  False indicates timeout."""
        assert not self._closed.isSet()
        return self._queue_is_empty.wait(timeout=timeout)

    def close(self):
        """Closes the associated serial port and shuts down worker thread"""
        assert not self._closed.isSet()

        with self._lock:
            self._closed.set()
            self._command_queue = []
            self._queue_is_empty.set()
            self._check_queue.set()

        if self._thread is not None:
            self._thread.join()

        self._ser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.description = "Send up, down, and stop commands to specified channels through Somfy Universal RTS Interface"
    parser.usage = "somfyrts.py <port> [options]"
    parser.add_argument('-up', type=int, nargs='+', metavar="#",
                        help="send up command to channel #")
    parser.add_argument('-down', type=int, nargs='+', metavar="#",
                        help="send down command to channel #")
    parser.add_argument('-stop', type=int, nargs='+', metavar="#",
                        help='send stop command to channel #')
    # noinspection SpellCheckingInspection
    parser.add_argument('-cmdver', type=int, choices=(1, 2), default=1,
                        help='universal rts interface version')
    parser.add_argument('-interval', type=float, default=1.5,
                        help="number of seconds to delay between sending commands (default is 1.5)")
    parser.add_argument('-pause', action='store_true',
                        help='pause [interval] seconds before sending first command')
    parser.add_argument('-verbose', action='store_true',
                        help="verbose output")
    parser.add_argument("port", type=str, help="url of serial port for rts controller communication")
    parser.epilog = "Valid channel numbers are 1 through 5 for a version one controller and 1 through 16 for version II"
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    if args.pause:
        logger.info("pausing {0} seconds before sending first command".format(args.interval))
        time.sleep(args.interval)

    with SomfyRTS(args.port, interval=args.interval, version=args.cmdver) as rts:
        rts.stop(args.stop)
        rts.up(args.up)
        rts.down(args.down)
