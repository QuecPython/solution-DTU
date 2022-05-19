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

    conf = {"1": {
                "protocol": "aliyun",
                "type": "mos",
                "keepAlive": "",
                "clientID": "0",
                "Devicename": "dtu_device1",
                "ProductKey": "gzsi5zT5fH3",
                "DeviceSecret": "173f006cab770615346978583ac430c0",
                "ProductSecret": "D07Ujh1RvKAs6KEY",
                "cleanSession": "0",
                "qos": "1",
                "subscribe": {"0": "/gzsi5zT5fH3/dtu_device1/user/get"},
                "publish": {"0": "/gzsi5zT5fH3/dtu_device1/user/update"},
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
    work_mode = "through"
    auto_connect = 1
    offline_storage = True
    modbus = {}
    