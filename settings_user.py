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

    password = ""

    conf = {"1": {
                "protocol": "quecthing",
                "keepAlive": "",
                "ProductKey": "p11js2",
                "ProductSecret": "VU5nVkNRNy9lOUNX",
                "Devicename": "dtudevice1",
                "DeviceSecret":"",
                "qos": "1",
                "SessionFlag": False,
                "sendMode": "pass",
                "serialID": "2"
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
    version = 100
    pins = ["", "", ""]
    direction_pin = {}
    apn = ["", "", ""]
    work_mode = "command"
    auto_connect = 1
    offline_storage = True
    modbus = {
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
    