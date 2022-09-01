#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@file      :serial.py
@author    :Chavis.Chen (chavis.chen@quectel.com)
@brief     :serial Tx & Rx implementations
@version   :0.1
@date      :2022-06-15 15:25:21
@copyright :Copyright (c) 2022
"""

from machine import UART
from machine import Timer
from queue import Queue
from usr.modules.logging import getLogger

class Serial(object):
    def __init__(self,
        uart,
        buadrate = 115200,
        databits = 8,
        parity = 0,
        stopbits = 1,
        flowctl = 0,
        rs485_direction_pin = ""):

        uart_port = getattr(UART, "UART%d" % int(uart))
        self._uart = UART(uart_port, buadrate, databits, parity, stopbits, flowctl)
        # init rs458 rx/tx pin
        if rs485_direction_pin != "":
            rs485_pin = getattr(UART, "GPIO%d" % int(rs485_direction_pin))
            self._uart.control_485(rs485_pin, 1)
        self._queue = Queue(maxsize = 1)
        self._timer = Timer(Timer.Timer1)
        self._log = getLogger(__name__)

        self._uart.set_callback(self._uart_cb)
        self.log_enable(False)

    def _uart_cb(self, args):
        self._log.debug("_uart_cb called with args:", args)
        if self._queue.size() == 0:
            self._log.debug("_uart_cb send a signal")
            self._queue.put(None)

    def _timer_cb(self, args):
        self._log.debug("_timer_cb called with args:", args)
        if self._queue.size() == 0:
            self._log.debug("_timer_cb send a signal")
            self._queue.put(None)

    def log_enable(self, en):
        if not isinstance(en, bool):
            return False

        if en:
            self._log.set_level("debug")
        else:
            self._log.set_level("critical")

        self._log.set_debug(en)
        return True

    def write(self, data):
        self._uart.write(data)

    def read(self, nbytes, timeout = 0):
        if nbytes == 0:
            return ''

        if self._uart.any() == 0 and timeout != 0:
            timer_started = False
            if timeout > 0: # < 0 for wait forever
                self._log.debug("start a timeout timer:", timeout)
                self._timer.start(period = timeout, mode = Timer.ONE_SHOT, callback = self._timer_cb)
                timer_started = True
            self._log.debug("wait for a signal")
            self._queue.get()
            if timer_started:
                self._timer.stop()

        r_data =  self._uart.read(min(nbytes, self._uart.any())).decode()
        if self._queue.size():
            self._log.debug("clean an extra signal")
            self._queue.get()

        return r_data