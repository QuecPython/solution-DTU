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
from usr.modules.common import Singleton

class DtuProtocolData(Singleton):

    def __init__(self):
        self.crc_table = []
        self._create_table()

    def _create_table(self):
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
        self.crc_table = a

    def crc32(self, crc_string):
        value = 0xffffffff
        for ch in crc_string:
            value = self.crc_table[(ord(ch) ^ value) & 0xff] ^ (value >> 8)
        crc_value = str((-1 - value) & 0xffffffff)
        return crc_value

    def package_datas(self, msg_data, topic_id=None, channel_id=None):
        print(msg_data)
        print("test691")

        data = []
        msg_length = len(str(msg_data))
        if channel_id is not None:
            data.append(str(channel_id))
        if topic_id is not None:
            data.append(str(topic_id))
        data.append(str(msg_length))
        print("test692")
        print("data array:", data)

        if len(msg_data) != 0:
            crc32_val = self.crc32(str(msg_data))
            data.append(crc32_val)
            data.append(str(msg_data))
       
        data_str = ",".join(data)
        ret_bytes = data_str.encode()
        print("ret_bytes:", ret_bytes)
            
        return ret_bytes

    def validate_length(self, data_len, msg_data, str_msg):
        if len(msg_data) < data_len:
            self.concat_buffer = str_msg
            self.wait_length = data_len - len(msg_data)
            print("wait length")
            print(self.wait_length)
            return False
        elif len(msg_data) > data_len:
            self.concat_buffer = ""
            self.wait_length = 0
            return False
        else:
            self.concat_buffer = ""
            self.wait_length = 0
            return True

