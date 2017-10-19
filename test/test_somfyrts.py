# ! python3
#
# This file is part of SomfyRTS - Universal RTS Interface for Somfy motors and controls
#
# (C) 2017 Ralph Lipe <ralph@lipe.ws>
#
# SPDX-License-Identifier:    MIT
"""\
Unit tests for SomfyRTS
"""

from datetime import datetime
from unittest import TestCase
from time import sleep

from somfyrts import SomfyRTS
from somfyrts.serialstub import SerialStub


# Simple class used for test assertions.
class Timer:
    def __init__(self):
        self._start_time = datetime.now()

    @property
    def elapsed(self) -> float:
        return (datetime.now() - self._start_time).total_seconds()


class TestSomfyRTS(TestCase):

    def test_up(self):
        ser = SerialStub()
        with SomfyRTS(ser, interval=0) as rts:
            rts.up(1)
            self.assertEqual(1, len(ser.output))
            self.assertEqual(b'U1\r', ser.output[0])

    def test_down(self):
        ser = SerialStub()
        with SomfyRTS(ser, interval=0) as rts:
            rts.down([1, 3])
            self.assertEqual(2, len(ser.output))
            self.assertEqual(b'D1\r', ser.output[0])
            self.assertEqual(b'D3\r', ser.output[1])

    def test_stop(self):
        ser = SerialStub()
        with SomfyRTS(ser, interval=0) as rts:
            rts.stop(None)
            self.assertEqual(0, len(ser.output))
            rts.stop([2, 5])
            self.assertEqual(2, len(ser.output))
            self.assertEqual(b'S2\r', ser.output[0])
            self.assertEqual(b'S5\r', ser.output[1])

    def test_close(self):
        ser = SerialStub()
        rts = SomfyRTS(ser, interval=0)
        rts.up(1)
        self.assertEqual(1, len(ser.output))
        self.assertEqual(b'U1\r', ser.output[0])
        rts.close()
        with self.assertRaises(AssertionError):
            rts.up(2)

    def test_multiple(self):
        ser = SerialStub()
        with SomfyRTS(ser, interval=0) as rts:
            rts.up(2)
            rts.down([1, 3])
            rts.stop(range(4, 6))
            self.assertEqual(5, len(ser.output))
            self.assertEqual(b'U2\r', ser.output[0])
            self.assertEqual(b'D1\r', ser.output[1])
            self.assertEqual(b'D3\r', ser.output[2])
            self.assertEqual(b'S4\r', ser.output[3])
            self.assertEqual(b'S5\r', ser.output[4])

    def test_version_2(self):
        ser = SerialStub()
        with SomfyRTS(ser, interval=0, version=2) as rts:
            rts.up(8)
            rts.down([12, 3])
            rts.stop([7, 16])
            self.assertEqual(5, len(ser.output))
            self.assertEqual(b'0108U', ser.output[0])
            self.assertEqual(b'0112D', ser.output[1])
            self.assertEqual(b'0103D', ser.output[2])
            self.assertEqual(b'0107S', ser.output[3])
            self.assertEqual(b'0116S', ser.output[4])

    def test_default_interval(self):
        ser = SerialStub()
        with SomfyRTS(ser) as rts:
            timer = Timer()
            rts.up(2)
            rts.down([1, 3])
            self.assertAlmostEqual(timer.elapsed, 3.0, places=1)
            self.assertEqual(3, len(ser.output))
            self.assertEqual(b'U2\r', ser.output[0])
            self.assertEqual(b'D1\r', ser.output[1])
            self.assertEqual(b'D3\r', ser.output[2])

    def test_interval(self):
        ser = SerialStub()
        with SomfyRTS(ser, interval=0.25) as rts:
            timer = Timer()
            rts.up(2)
            rts.down([1, 3])
            rts.stop(range(4, 6))
            self.assertAlmostEqual(timer.elapsed, 1.0, places=1)
            self.assertEqual(5, len(ser.output))
            self.assertEqual(b'U2\r', ser.output[0])
            self.assertEqual(b'D1\r', ser.output[1])
            self.assertEqual(b'D3\r', ser.output[2])
            self.assertEqual(b'S4\r', ser.output[3])
            self.assertEqual(b'S5\r', ser.output[4])

    def test_flush_command_queue(self):
        ser = SerialStub()
        with SomfyRTS(ser, interval=0.25, thread=True) as rts:
            timer = Timer()
            rts.up(2)
            rts.down([1, 3])
            rts.stop(range(4, 6))
            self.assertAlmostEqual(timer.elapsed, 0.0, places=1)
            rts.flush_command_queue()
            self.assertAlmostEqual(timer.elapsed, 1.0, places=1)
            self.assertEqual(5, len(ser.output))
            self.assertEqual(b'U2\r', ser.output[0])
            self.assertEqual(b'D1\r', ser.output[1])
            self.assertEqual(b'D3\r', ser.output[2])
            self.assertEqual(b'S4\r', ser.output[3])
            self.assertEqual(b'S5\r', ser.output[4])

    def test_clear_command_queue(self):
        ser = SerialStub()
        with SomfyRTS(ser, interval=1.0, thread=True) as rts:
            timer = Timer()
            rts.up(2)
            rts.down([1, 3])
            rts.stop(range(4, 6))
            self.assertAlmostEqual(timer.elapsed, 0.0, places=1)
            sleep(1.5)  # Up 2 and Down 1 should make it but no more by now.
            rts.clear_command_queue()
            self.assertEqual(2, len(ser.output))
            self.assertEqual(b'U2\r', ser.output[0])
            self.assertEqual(b'D1\r', ser.output[1])

    def test_close_threaded(self):
        ser = SerialStub()
        rts = SomfyRTS(ser, interval=1.0, thread=True)
        rts.up([1, 2, 3])
        sleep(0.5)
        self.assertEqual(1, len(ser.output))
        self.assertEqual(b'U1\r', ser.output[0])
        rts.close()
        sleep(3.0)
        self.assertEqual(1, len(ser.output))

    def test_fast_close(self):
        ser = SerialStub()
        rts = SomfyRTS(ser, interval=20.0, thread=True)
        timer = Timer()
        rts.up([1, 2, 3])
        sleep(0.5)
        self.assertEqual(1, len(ser.output))
        self.assertEqual(b'U1\r', ser.output[0])
        rts.close()
        self.assertAlmostEqual(timer.elapsed, 0.5, places=1)
        self.assertEqual(1, len(ser.output))
