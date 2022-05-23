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


class UserConfig(object):
    plate = 1

    password = "123"

    conf = {"1": 
                {
                "protocol": "udp",
                "ping": "",
                "heartbeat": 30,
                "url": "220.180.239.212",
                "port": "8305",
                "keepAlive": 300,
                "serialID": 2
                }
            }
    reg = 0
    convert = 0
    nolog = 0
    message = {}
    uconf = {"2": {
                "baudrate": "115200",
                "databits": "8",
                "parity": "0",
                "stopbits": "1",
                "flowctl": "0"
                }
            }
    fota = 1
    ota = 1
    pins = ["1", "2", "3"]
    direction_pin = {}
    apn = ["", "", ""]
    work_mode = "command"
    auto_connect = 1
    offline_storage = True
    modbus = {}
    