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
@file      :modbus_mode.py
@author    :elian.wang@quectel.com
@brief     :Dtu function interface that works in Modbus mode
@version   :0.1
@date      :2022-05-23 09:04:00
@copyright :Copyright (c) 2022
"""


import ujson
import utime
import ubinascii
from usr.modules.common import Singleton
from usr.modules.logging import error_map
from usr.modules.logging import RET
from usr.modules.logging import getLogger

log = getLogger(__name__)

def modbus_crc(string_byte):
    crc = 0xFFFF
    for pos in string_byte:
        crc ^= pos
        for i in range(8):
            if ((crc & 1) != 0):
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1
    gen_crc = hex(((crc & 0xff) << 8) + (crc >> 8))
    int_crc = int(gen_crc, 16)
    high, low = divmod(int_crc, 0x100)
    string_byte.append(high)
    string_byte.append(low)
    return string_byte


class ModbusMode(Singleton):
    def __init__(self, mode, modbus_conf):
        print("modbusCMD start")
        self.modbus_conf = None
        self.__protocol = None
        if mode == "modbus":
            self.modbus_conf = modbus_conf
            print(self.modbus_conf)
            self.groups = dict()
            self._load_groups()

    def set_protocol(self, protocol):
        self.__protocol = protocol

    def _load_groups(self):
        print("modbus load groups")
        groups_conf = self.modbus_conf.get("groups", [])
        idx = 0
        print(groups_conf)
        for group in groups_conf:
            print(group)
            self.groups[idx] = [int(x, 16) for x in group["slave_address"]]
            idx += 1

    def cloud_data_parse(self, data, topic_id, channel_id):
        ret_data = {"cloud_data":None, "uart_data":None}
        print("data:{}".format(data))
        print("data type:{}".format(type(data)))
        try:
            if isinstance(data, str):
                msg_data = ujson.loads(data)
            elif isinstance(data, bytes):
                msg_data = ujson.loads(str(data))
            elif isinstance(data, dict):
                msg_data = data
            else:
                raise error_map.get(RET.CMDPARSEERR)
            modbus_data = msg_data.get("modbus", None)
            if modbus_data is not None:
                if "groups" in modbus_data:
                    groups_num = modbus_data["groups"].get("num")
                    cmd = modbus_data["groups"].get("cmd")
                    try:
                        int_cmd = [int(x, 16) for x in cmd]
                    except Exception as e:
                        log.info("modbus command error: %s" % e)
                        ret_data["cloud_data"] = {"status": 0, "error": e}
                    groups_addr = self.groups.get(int(groups_num))
                    for addr in groups_addr:
                        modbus_cmd = [addr]
                        modbus_cmd.extend(int_cmd)
                        crc_cmd = modbus_crc(bytearray(modbus_cmd))
                        print(crc_cmd)
                        ret_data["uart_data"] = crc_cmd
                        utime.sleep(1)
                    ret_data["cloud_data"] = {"code": cmd, "status": 1}
                elif "command" in data:
                    command = modbus_data["command"]
                    try:
                        int_cmd = [int(x, 16) for x in command]
                        crc_cmd = modbus_crc(bytearray(int_cmd))
                    except Exception as e:
                        log.info("modbus command error: %s" % e)
                        ret_data["cloud_data"] = {"status": 0, "error": e}
                    print("modbus write cmd")
                    print(crc_cmd)
                    ret_data["uart_data"] = crc_cmd
                    ret_data["cloud_data"] = {"code": command, "status": 1}
                else:
                    err_msg = "can't get any modbus params"
                    print(err_msg)
                    ret_data["cloud_data"] = {"code": 0, "status": 0, "error": err_msg}
            return ret_data
        except Exception as e:
                log.info("{}: {}".format(error_map.get(RET.CMDPARSEERR), e))

    def uart_data_parse(self, data, cloud_channel_dict, cloud_channel_array=None):
        str_msg = ubinascii.hexlify(data, ",").decode()
        # Modbus模式和透传模式 下一个串口通道只能绑定一个云端口
        cloud_channel_id = cloud_channel_array[0]
        channel = cloud_channel_dict.get(str(cloud_channel_id))
        if not channel:
            print("Channel id not exist. Check serialID config.")
            return False, []
        print("modbus str_msg")
        print(type(str_msg))
        print(str_msg)
        modbus_data_list = str_msg.split(",")
        hex_list = ["0x" + x for x in modbus_data_list]
        # 返回channel
        if channel.get("protocol") in ["http", "tcp", "udp", "quecthing"]:
            return hex_list, [cloud_channel_id]
        else:
            topics = list(channel.get("publish").keys())
            return hex_list, [cloud_channel_id, topics[0]]