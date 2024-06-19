# Copyright (c) Quectel Wireless Solution, Co., Ltd.All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.from machine import I2C

#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@file      :temp_humidity_sensor.py
@author    :elian.wang@quectel.com
@brief     :Show tempurature and humidity sensor TH20 usage
@version   :0.1
@date      :2022-05-20 11:14:24
@copyright :Copyright (c) 2022
"""

import utime as time
from machine import I2C

class TempHumiditySensor:
    """Read tempurature and humidity sensor value,reset sensor
    """
    def __init__(self):
        self.__i2c = I2C(I2C.I2C1, I2C.STANDARD_MODE)
        self.__data_cache = None
        # Initialization command
        self.__CALIBRATION_CMD = 0xE1
        # Trigger measurement
        self.__START_MEASURMENT_CMD = 0xAC
        # reset
        self.__RESET_CMD = 0xBA
        # slave address
        self.__i2c_addr = 0X38
        self.init()
    
    def __write_data(self, data):
        self.__i2c.write(self.__i2c_addr,
                       bytearray(0x00), 0,
                       bytearray(data), len(data))

    def __read_data(self, length):
        r_data = [0x00 for i in range(length)]
        r_data = bytearray(r_data)
        self.__i2c.read(self.__i2c_addr,
                      bytearray(0x00), 0,
                      r_data, length,
                      0)
        return list(r_data)        

    def __get_datas(self, length):
        # Trigger data conversion,send 0xAC, 0x33， 0x00
        self.__write_data([self.__START_MEASURMENT_CMD, 0x33, 0x00])
        time.sleep_ms(200)  # at last delay 75ms
        self.__data_cache = self.__read_data(length)

    def __humidity_transformat(self):
        data = self.__data_cache[1:6]
        humidity = (data[0] << 12) | (
                data[1] << 4) | ((data[2] & 0xF0) >> 4)
        return round((humidity / (1 << 20)) * 100.0, 2)

    def __temperature_transformat(self):
        data = self.__data_cache[1:6]
        temperature = ((data[2] & 0xf) << 16) | (
                data[3] << 8) | data[4]
        return round((temperature * 200.0 / (1 << 20)) - 50, 2)

    def init(self):
        self.__write_data([self.__CALIBRATION_CMD, 0x08, 0x00])
        time.sleep_ms(300)  # at last 300ms

    def reset(self):
        self.__write_data([self.__RESET_CMD])
        time.sleep_ms(20)  # at last 20ms

    def read_temperature(self):
        self.__get_datas(6)
        # check bit7
        if (self.__data_cache[0] >> 7) != 0x0:
            pass
            return False
        temperature = self.__temperature_transformat()
        return temperature

    def read_humidity(self):
        self.__get_datas(6)
        if (self.__data_cache[0] >> 7) != 0x0:
            pass
            return False
        humidity = self.__humidity_transformat()
        return humidity

    def read(self):
        self.__get_datas(6)
        if (self.__data_cache[0] >> 7) != 0x0:
            pass
            return False
        return self.__temperature_transformat(), self.__humidity_transformat()

