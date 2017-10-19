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
import time

from somfyrts import SomfyRTS
from somfyrts.serialstub import SerialStub

import logging
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.description = "Send up, down, and stop commands to specified channels through Somfy Universal RTS Interface"
    parser.usage = "python3 -m somfyrts <port> [-h] [options]"
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
    parser.epilog = "Valid channel numbers are 1 through 5 for a version one controller and 1 through 16 " + \
                    "for the version II controller.  For testing purposes the port name 'TEST' can be used."
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    if args.pause:
        logger.info("pausing {0} seconds before sending first command".format(args.interval))
        time.sleep(args.interval)

    port = args.port if args.port != "TEST" else SerialStub()

    with SomfyRTS(port, interval=args.interval, version=args.cmdver) as rts:
        rts.stop(args.stop)
        rts.up(args.up)
        rts.down(args.down)
