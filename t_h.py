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

import utime as time


class SensorTH:

    def __init__(self):
        # super(SensorTH, self).__init__()
        self.i2cn = I2C.I2C1
        self.i2c_mode = I2C.STANDARD_MODE
        self.i2c = I2C(self.i2cn, self.i2c_mode)
        self.data_cache = None
        self._init_cmd()
        self.sensor_init()

    def _init_cmd(self):
        # Initialization command
        self.CALIBRATION_CMD = 0xE1
        # Trigger measurement
        self.START_MEASURMENT_CMD = 0xAC
        # reset
        self.RESET_CMD = 0xBA
        # slave address
        self.i2c_addr = 0X38

    def write_data(self, data):
        self.i2c.write(self.i2c_addr,
                       bytearray(0x00), 0,
                       bytearray(data), len(data))

    def read_data(self, length):
        r_data = [0x00 for i in range(length)]
        r_data = bytearray(r_data)
        self.i2c.read(self.i2c_addr,
                      bytearray(0x00), 0,
                      r_data, length,
                      0)
        return list(r_data)

    def sensor_init(self):
        # 上电等待校准数据。 发送 0xE1 0x08 0x00
        self.write_data([self.CALIBRATION_CMD, 0x08, 0x00])
        time.sleep_ms(300)  # at last 300ms

    def sensor_reset(self):
        self.write_data([self.RESET_CMD])
        time.sleep_ms(20)  # at last 20ms

    def _get_datas(self, length):
        # Trigger data conversion
        # 触发测量，发送 0xAC, 0x33， 0x00
        self.write_data([self.START_MEASURMENT_CMD, 0x33, 0x00])
        time.sleep_ms(200)  # at last delay 75ms
        data = [0x00 for i in range(length)]
        data = bytearray(data)
        self.i2c.read(self.i2c_addr,
                      bytearray(0x00), 0,
                      data, length, 0)
        self.data_cache = list(data)

    def _humidity_transformat(self):
        data = self.data_cache[1:6]
        humidity = (data[0] << 12) | (
                data[1] << 4) | ((data[2] & 0xF0) >> 4)
        return round((humidity / (1 << 20)) * 100.0, 2)

    def _temperature_transformat(self):
        data = self.data_cache[1:6]
        temperature = ((data[2] & 0xf) << 16) | (
                data[3] << 8) | data[4]
        return round((temperature * 200.0 / (1 << 20)) - 50, 2)

    def read_temperature(self):
        # self.sensor_reset()
        self._get_datas(6)
        # check bit7
        if (self.data_cache[0] >> 7) != 0x0:
            pass
            return False
        temperature = self._temperature_transformat()
        return temperature

    def read_humidity(self):
        # self.sensor_reset()
        self._get_datas(6)
        if (self.data_cache[0] >> 7) != 0x0:
            pass
            return False
        humidity = self._humidity_transformat()
        return humidity

    def read(self):
        # self.sensor_reset()
        self._get_datas(6)
        if (self.data_cache[0] >> 7) != 0x0:
            pass
            return False
        return self._temperature_transformat(), self._humidity_transformat()

