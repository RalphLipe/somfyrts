# Simple class that supports a subset of the Serial interface used for testing puposes
#
# Copyright (C) 2017 Ralph Lipe <ralph@lipe.ws>
#
# SPDX-License-Identifier:    MIT


from serial import SerialException

class SerialStub:
    TEST_PORT_NAME = "TEST"

    def __init__(self):
        self.output = []
        self.is_open = True

    def write(self, data):
        if self.is_open:
            self.output.append(data)
        else:
            raise SerialException("SerialStub closed when write method called")

    def close(self):
        self.is_open = False

