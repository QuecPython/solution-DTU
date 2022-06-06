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
from usr.settings import settings
from usr.modules.common import Singleton
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
    """When working in modbus mode, the DTU process cloud data and uart data

    This class has the following functions:
        1.Parse cloud publish data
        2.Parse the data read from uart
    Attribute:
        __modbus_conf(dict):modbus configs
        modbus configs format:
        {
            "groups":
            [        
                {
                    "device_type": "temp_humid_sensor",     
                    "device_model": "TH10S-B",             
                    "slave_address":["0x01"]             
                },
                {
                    "device_type": "light_sensor",
                    "device_model": "YGC-BG-M",
                    "slave_address":["0x02", "0x03"]
                }
            ]
        }

        __groups(list):slave address list
    """
    def __init__(self):
        self.__groups = dict()
        current_settings = settings.get()
        groups_conf = current_settings.get("modbus").get("groups", [])
        idx = 0
        for group in groups_conf:
            self.__groups[idx] = [int(x, 16) for x in group["slave_address"]]
            idx += 1

    def cloud_data_parse(self, data, topic_id, channel_id):
        """Parse the data read from cloud

        Args:
            data (bytes): Data read from the serial port
            topic_id (str): cloud config dict 
            channel_id(str): Cloud channel list corresponding to uart channel 

        Returns:
            dict: Data that has been processed,wait to send to cloud or uart
        """
        ret_data = {"cloud_data":None, "uart_data":None}
        try:
            if isinstance(data, str):
                msg_data = ujson.loads(data)
            elif isinstance(data, bytes):
                msg_data = ujson.loads(str(data))
            elif isinstance(data, dict):
                msg_data = data
            else:
                raise Exception("Cloud data parse error")
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
                    groups_addr = self.__groups.get(int(groups_num))
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
                    ret_data["uart_data"] = crc_cmd
                    ret_data["cloud_data"] = {"code": command, "status": 1}
                else:
                    err_msg = "can't get any modbus params"
                    log.error("Modbus mode: can't get any modbus params")
                    ret_data["cloud_data"] = {"code": 0, "status": 0, "error": err_msg}
            return ret_data
        except Exception as e:
                log.info("command parse error transfer to modbus: {}".format(e))
                return ret_data

    def uart_data_parse(self, data, cloud_channel_dict, cloud_channel_array=None):
        """Parse the data read from uart

        Args:
            data (bytes): Data read from the serial port
            cloud_channel_dict (dict): cloud config dict 
            cloud_channel_array(list): Cloud channel list corresponding to uart channel 
        Returns:
            list: 1.msg_data:Data that has been processed,wait to send to cloud
                  2.cloud_channel_id:cloud channel id 
                  3.topic_id:toic id of data
        """
        str_msg = ubinascii.hexlify(data, ",").decode()
        # Modbus模式和透传模式 下一个串口通道只能绑定一个云端口
        cloud_channel_id = cloud_channel_array[0]
        channel = cloud_channel_dict.get(str(cloud_channel_id))
        if not channel:
            print("Channel id not exist. Check serialID config.")
            return False, []
        modbus_data_list = str_msg.split(",")
        hex_str_list = ["0x" + x for x in modbus_data_list]
        # 返回channel
        if channel.get("protocol") in ["http", "tcp", "udp", "quecthing"]:
            return [str(hex_str_list), cloud_channel_id]
        else:
            topics = list(channel.get("publish").keys())
            return [str(hex_str_list), cloud_channel_id, topics[0]]