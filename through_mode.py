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
from usr.dtu_crc import dtu_crc

log = getLogger(__name__)

class ThroughMode(Singleton):
    """When Dtu work in through mode, the method of processing data
        This class has the following functions
        1.Parse cloud publish data
        2.Parse the data read from uart
    """

    def __package_datas(self, msg_data, topic_id=None):
        """Package downsteam data

        Args:
            msg_data (str): Data that needs to be send
            topic_id (str): Topic id of data to be sent.

        Returns:
            bytes: Complete the packaged data
        """
        if msg_data is not None:
            msg_length = len(str(msg_data))
            crc32_val = dtu_crc.crc32(str(msg_data))
            if topic_id == None: # tcp\udp
                ret_bytes = "%s,%s,%s".encode('utf-8') % (str(msg_length), str(crc32_val), str(msg_data))
            else:
                ret_bytes = "%s,%s,%s,%s".encode('utf-8') % (str(topic_id), str(msg_length), str(crc32_val), str(msg_data))
        else:
            ret_bytes = None
        print("ret_bytes:", ret_bytes)
            
        return ret_bytes

    def cloud_data_parse(self, data, topic_id, channel_id):
        """Parse cloud publish data

        Args:
            data (str): cloud publish data
            topic_id (str): toic id of data
            channel_id (str): cloud channel id 

        Returns:
            dict: Data that has been processed,wait to send to cloud or uart 
        """
        ret_data = {"cloud_data":None, "uart_data":None}

        if isinstance(data, (int, float)):
            data = str(data)
        package_data = self.__package_datas(data, topic_id)
        log.info("package_data:", package_data)
        ret_data["uart_data"] = package_data
        return ret_data

    def uart_data_parse(self, data, cloud_channel_dict, cloud_channel_array=None):
        """Parse the data read from uart

        Args:
            data (bytes):  Data read from the serial port
            cloud_channel_dict (dict): cloud config dict 
            cloud_channel_array(list): Cloud channel list corresponding to uart channel 
        Returns:
            list: 1.msg_data:Data that has been processed,wait to send to cloud
                  2.cloud_channel_id:cloud channel id 
                  3.topic_id:toic id of data
        """
        # Modbus模式和透传模式 下一个串口通道只能绑定一个云端口
        cloud_channel_id = cloud_channel_array[0]
        channel = cloud_channel_dict.get(str(cloud_channel_id))
        if not channel:
            log.error("Channel id not exist. Check serialID config.")
            return []
        print("channel.get(protocol):", channel.get("protocol"))
        if channel.get("protocol") in ["tcp", "udp"]:
            params_list = data.decode().split(",", 2)
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
                    return []
                # Message length check
                if msg_len_int != len(msg_data):
                    return []
                cal_crc32 = dtu_crc.crc32(msg_data)
                if cal_crc32 == crc32:
                    return [msg_data, cloud_channel_id]
                else:
                    log.error("crc32 error")
                    return []
        else:
            params_list = data.decode().split(",", 3)
            topic_id = params_list[0]
            msg_len = params_list[1]
            crc32 = params_list[2]
            msg_data = params_list[3]
            try:
                msg_len_int = int(msg_len)
            except:
                log.error("data parse error")
                return []
            # Message length check
            if msg_len_int != len(msg_data):
                return []
            cal_crc32 = dtu_crc.crc32(msg_data)
            if crc32 == cal_crc32:
                return [msg_data, cloud_channel_id, topic_id]
            else:
                return []