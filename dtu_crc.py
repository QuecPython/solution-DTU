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
# limitations under the License.

#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@file      :dtu_crc.py
@author    :elian.wang@quectel.com
@brief     :When dtu package downsteam data, perform Crc calculations
@version   :0.1
@date      :2022-05-26 10:32:09
@copyright :Copyright (c) 2022
"""


from usr.modules.common import Singleton

class DtuCrc(Singleton):
    """This class is dtu package downsteam data

        This class has the following functions
        1.Perform CRC check on data
    """

    def __init__(self):
        self.__crc_table = []
        self.__create_table()

    def __create_table(self):
        poly = 0xEDB88320
        a = []
        for byte in range(256):
            crc = 0
            for bit in range(8):
                if (byte ^ crc) & 1:
                    crc = (crc >> 1) ^ poly
                else:
                    crc >>= 1
                byte >>= 1
            a.append(crc)
        self.__crc_table = a

    def crc32(self, crc_string):
        value = 0xffffffff
        for ch in crc_string:
            value = self.__crc_table[(ord(ch) ^ value) & 0xff] ^ (value >> 8)
        crc_value = str((-1 - value) & 0xffffffff)
        return crc_value

dtu_crc = DtuCrc() 