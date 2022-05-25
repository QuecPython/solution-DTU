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

"""
@file      :through_mode.py
@author    :elian.wang@quectel.com
@brief     :Dtu function interface that works in through mode
@version   :0.1
@date      :2022-05-23 09:04:00
@copyright :Copyright (c) 2022
"""

from usr.modules.common import Singleton
from usr.modules.logging import getLogger

log = getLogger(__name__)

class ThroughMode(Singleton):
    def __init__(self):
        self.__protocol = None

    def set_protocol(self, protocol):
        self.__protocol = protocol

    def cloud_data_parse(self, data, topic_id, channel_id):
        ret_data = {"cloud_data":None, "uart_data":None}

        if isinstance(data, (int, float)):
            data = str(data)
        package_data = self.__protocol.package_datas(data, topic_id)
        print("package_data:", package_data)
        ret_data["uart_data"] = package_data
        return ret_data

    def uart_data_parse(self, data, cloud_channel_dict, cloud_channel_array=None):
        str_msg = data.decode()
        params_list = str_msg.split(",")
        print("params_list", params_list)
        if len(params_list) not in [2, 3, 4]:
            log.error("param length error")
            return False, []
        # Modbus模式和透传模式 下一个串口通道只能绑定一个云端口
        cloud_channel_id = cloud_channel_array[0]
        channel = cloud_channel_dict.get(str(cloud_channel_id))
        if not channel:
            log.error("Channel id not exist. Check serialID config.")
            return False, []
        print("channel.get(protocol):", channel.get("protocol"))
        if channel.get("protocol") in ["tcp", "udp"]:
            msg_len = params_list[0]
            if msg_len == "0":
                return "", [cloud_channel_id]
            else:
                crc32 = params_list[1]
                msg_data = params_list[2]
                try:
                    msg_len_int = int(msg_len)
                except:
                    log.error("data parse error")
                    return False, []
                # Message length check
                if msg_len_int != len(msg_data):
                    return False, []
                cal_crc32 = self.__protocol.crc32(msg_data)
                if cal_crc32 == crc32:
                    return msg_data, [cloud_channel_id]
                else:
                    log.error("crc32 error")
                    return False, []
        else:
            print("test23")
            topic_id = params_list[0]
            msg_len = params_list[1]
            crc32 = params_list[2]
            msg_data = params_list[3]
            try:
                msg_len_int = int(msg_len)
            except:
                log.error("data parse error")
                return False, []
            # Message length check
            if msg_len_int != len(msg_data):
                return False, []
            print("test24")
            cal_crc32 = self.__protocol.crc32(msg_data)
            if crc32 == cal_crc32:
                return msg_data, [cloud_channel_id, topic_id]
            else:
                return False, []