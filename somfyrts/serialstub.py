#!/usr/bin/env python3
#
# Simple serial port stub used for testing.
#
# Copyright (C) 2017 Ralph Lipe <ralph@lipe.ws>
#
# SPDX-License-Identifier:    MIT
"""\
Serial testing support.
"""
import threading


class SerialStub:

    def __init__(self):
        self.output = []
        self.is_open = True
        self._lock = threading.Lock()
        self._check_read_queue = threading.Event()
        self._read_queue = bytearray()
        self._read_canceled = False

    def write(self, data):
        if self.is_open:
            self.output.append(data)
        else:
            raise Exception("SerialStub closed when write method called")

    @property
    def in_waiting(self):
        with self._lock:
            return len(self._read_queue)

    def read(self, size=1):
        while self._check_read_queue.wait():
            with self._lock:
                if self._read_canceled:
                    return None
                if len(self._read_queue) >= size:
                    result = self._read_queue[:size]
                    self._read_queue = self._read_queue[size:]
                    return result
                else:   # Not enough data for request
                    self._check_read_queue.clear()

    def cancel_read(self):
        with self._lock:
            self._read_canceled = True
            self._check_read_queue.set()

    def queue_data_for_read(self, data):
        with self._lock:
            self._read_queue += data
            self._check_read_queue.set()

    def close(self):
        with self._lock:
            self.is_open = False
