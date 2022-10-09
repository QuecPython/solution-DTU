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
    system_config = {
        "cloud": "aliyun",
        "usr_config": False,
        "base_function":
		{
			"logger": True,
            "offline_storage": True,
            "fota":True,
            "sota":True
		},
    }
    usr_config = {}
    aliyun_config = {
        "server": "gzsi5zT5fH3.iot-as-mqtt.cn-shanghai.aliyuncs.com",
		"DK": "dtu_device1",
        "PK": "gzsi5zT5fH3",
        "DS": "173f006cab770615346978583ac430c0",
        "PS": "D07Ujh1RvKAs6KEY",
		"burning_method": 1,
		"keep_alive": 300,
		"clean_session": False,
		"qos": 1,
        "client_id":"",
        "subscribe": {"0": "/gzsi5zT5fH3/dtu_device1/user/get"},
        "publish": {"0": "/gzsi5zT5fH3/dtu_device1/user/update"}
    }
    txyun_config = {
        "DK": "dtu_device1",
        "PK": "I81T7DUSFF",
        "DS": "wF+b5NwEHI53crHmOqdyQA==",
        "PS": "",
		"burning_method": 1,
		"keep_alive": 300,
		"clean_session": False,
		"qos": 1,
        "client_id":"",
        "subscribe": {"0": "I81T7DUSFF/dtu_device1/control"},
        "publish": {"0": "I81T7DUSFF/dtu_device1/event"}
    }
    hwyun_config = {
        "server": "a15fbbd7ce.iot-mqtts.cn-north-4.myhuaweicloud.com",
        "port": "1883",
		"DK": "625132b420cfa22b94c54613_dtu_device1_id",
        "PK": "",
        "DS": "a306255686a71e56ad53965fc2771bf8",
        "PS": "",
		"keep_alive": 300,
		"clean_session": False,
		"qos": 1,
        "subscribe": {"0": "$oc/devices/625132b420cfa22b94c54613_dtu_device1_id/sys/messages/down"},
        "publish": {"0": "$oc/devices/625132b420cfa22b94c54613_dtu_device1_id/sys/messages/up"}
    }
    quecthing_config = {
        "server":"iot-south.quectel.com",
        "port": "1883",
		"DK": "dtudevice1",
        "PK": "p11js2",
        "DS": "",
        "PS": "VU5nVkNRNy9lOUNX",
		"keep_alive": 300,
		"clean_session": False,
		"qos": 1
    }
    tcp_private_cloud_config = {
        "ip_type":"IPv4",
        "server": "a15fbbd7ce.iot-mqtts.cn-north-4.myhuaweicloud.com",
        "port": "1883",
        "keep_alive": 5
    }
    mqtt_private_cloud_config = {
        "server": "a15fbbd7ce.iot-mqtts.cn-north-4.myhuaweicloud.com",
        "port": "1883",
        "client_id": "test_mqtt",
        "clean_session": False,
        "qos": "0",
        "keep_alive": 300,
        "subscribe": {"0": "oc/devices/625132b420cfa22b94c54613_dtu_device1_id/sys/messages/down"},
        "publish": {"0": "oc/devices/625132b420cfa22b94c54613_dtu_device1_id/sys/messages/up"}
    }
    uart_config = {
        "port" : "2",
        "baudrate": "115200",
        "databits": "8",
        "parity": "0",
        "stopbits": "1",
        "flowctl": "0",
        "rs485_direction_pin": ""
    }