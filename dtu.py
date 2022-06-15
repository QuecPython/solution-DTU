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
@file      :dtu.py
@author    :elian.wang@quectel.com
@brief     :dtu main function
@version   :0.1
@date      :2022-05-18 09:12:37
@copyright :Copyright (c) 2022
"""

import sim, dataCall, net, modem, utime, _thread
from usr.modules.common import Singleton
from usr.modules.aliyunIot import AliYunIot
from usr.modules.quecthing import QuecThing
from usr.modules.mqttIot import MqttIot
from usr.modules.huawei_cloud import HuaweiIot
from usr.modules.txyunIot import TXYunIot
from usr.modules.requestIot import DtuRequest
from usr.modules.tcp_udpIot import TcpSocketIot
from usr.modules.tcp_udpIot import UdpSocketIot


from usr.dtu_gpio import Gpio
from usr.settings import settings
from usr.command_modbus_mode import CommandModbusMode
from usr.through_mode import ThroughMode
from usr.modules.history import History
from usr.modules.logging import getLogger
from usr.dtu_channels import ChannelTransfer
from usr.dtu_data_process import DtuDataProcess
from usr.modules.remote import RemotePublish, RemoteSubscribe
from usr.settings import PROJECT_NAME, PROJECT_VERSION, DEVICE_FIRMWARE_NAME, DEVICE_FIRMWARE_VERSION



log = getLogger(__name__)


class Dtu(Singleton):

    def __init__(self):
        self.__gpio = None
        self.__data_process = None
        self.__channel = None
        self.__history = None

    def add_module(self, module):
        if isinstance(module, Gpio):
            self.__gpio = module
            return True
        elif isinstance(module, DtuDataProcess):
            self.__data_process = module
            return True
        elif isinstance(module, ChannelTransfer):
            self.__channel = module
            return True
        elif isinstance(module, History):
            self.__history = module
            return True
        return False


    def check_sim_status(self):
        ret = sim.getStatus()
        while True:
            if sim.getStatus() != 1:
                self.__gpio.ctrl_led(1)
                utime.sleep(1)
                self.__gpio.ctrl_led(0)
                utime.sleep(1)
            else:
                self.__gpio.ctrl_led(0)
                break

    def dialing(self, apn):
        log.info("apn", apn)
        if apn[0] != "" and apn[1] != "" and apn[2] != "":
            call_count = 0
            while True:
                res = dataCall.setApn(1, 0, apn[0], apn[1], apn[2], 0)
                if res == 0:
                    log.info("APN datacall successful")
                    break
                if res == -1:
                    log.info("Try APN datacall...")
                    call_count += 1
                    utime.sleep(1)
                    if call_count > 10:
                        log.error("Datacall failed, please restart device and run again.")
                        break
        else:
            pass #默认apn在固件实现
        
        # 检查拨号结果,拨号失败闪烁LED灯
        while True:
            if dataCall.getInfo(1, 0)[2][0] == 0:
                self.__gpio.ctrl_led(1)
                utime.sleep(1)
                self.__gpio.ctrl_led(0)
                utime.sleep(1)
            else:
                self.__gpio.ctrl_led(0)
                break
        

    def cloud_init(self, serv_list, remote_sub, remote_pub):
        print("serv_list:",serv_list)

        # 首次登陆服务器默认注册信息
        reg_data = {"csq": net.csqQueryPoll(), 
                    "imei": modem.getDevImei(), 
                    "iccid": sim.getIccid(),
                    "ver": PROJECT_VERSION}  

        for cid, data in serv_list.items():
            if not data:
                continue
            protocol = data.get("protocol").lower()
            if protocol == "mqtt":
                mqtt_iot = MqttIot(data.get("url", None),
                                    int(data.get("qos", 0)),
                                    int(data.get("port", 1883)),
                                    data.get("cleanSession"),
                                    data.get("clientID"),
                                    data.get("publish"),
                                    data.get("subscribe")
                                    )
                mqtt_iot.init(enforce=True)
                mqtt_iot.addObserver(remote_sub)
                remote_pub.add_cloud(mqtt_iot, cid)
                self.__channel.cloud_object_dict[cid] = mqtt_iot
            elif protocol == "aliyun":
                dtu_ali = AliYunIot(data.get("ProductKey"),
                                    data.get("ProductSecret"),
                                    data.get("Devicename"),
                                    data.get("DeviceSecret"),
                                    ("%s.iot-as-mqtt.cn-shanghai.aliyuncs.com" % data.get("ProductKey")),
                                    int(data.get("qos", 0)),
                                    data.get("clientID"),
                                    data.get("publish"),
                                    data.get("subscribe"),
                                    burning_method = (1 if data.get("type") == "mos" else 0),
                                    mcu_name=PROJECT_NAME,
                                    mcu_version=PROJECT_VERSION,
                                    firmware_name=DEVICE_FIRMWARE_NAME,
                                    firmware_version=DEVICE_FIRMWARE_VERSION
                                    )
                dtu_ali.init(enforce=True)
                dtu_ali.addObserver(remote_sub)
                remote_pub.add_cloud(dtu_ali, cid)
                self.__channel.cloud_object_dict[cid] = dtu_ali
            elif protocol.startswith("quecthing"):
                quec_req = QuecThing(data.get("ProductKey"),
                                     data.get("ProductSecret"),
                                     data.get("Devicename"),
                                     data.get("DeviceSecret"),
                                     "iot-south.quectel.com:1883",
                                     int(data.get("qos", 0)),
                                     mcu_name=PROJECT_NAME,
                                     mcu_version=PROJECT_VERSION)
                quec_req.init(enforce=True)
                quec_req.addObserver(remote_sub)
                remote_pub.add_cloud(quec_req, cid)
                self.__channel.cloud_object_dict[cid] = quec_req
            elif protocol == "txyun":
                dtu_txyun = TXYunIot(data.get("ProductKey"),
                                    data.get("ProductSecret"),
                                    data.get("Devicename"),
                                    data.get("DeviceSecret"),
                                    data.get("cleanSession", False),
                                    data.get("clientID"),
                                    data.get("publish"),
                                    data.get("subscribe"),
                                    burning_method = (1 if data.get("type") == "mos" else 0),
                                    mcu_name=PROJECT_NAME,
                                    mcu_version=PROJECT_VERSION,
                                    firmware_name=DEVICE_FIRMWARE_NAME,
                                    firmware_version=DEVICE_FIRMWARE_VERSION
                                    )
                dtu_txyun.init(enforce=True)
                dtu_txyun.addObserver(remote_sub)
                remote_pub.add_cloud(dtu_txyun, cid)
                self.__channel.cloud_object_dict[cid] = dtu_txyun
            elif protocol == "hwyun":
                huawei_iot = HuaweiIot(data.get("ProductKey", None),
                                    data.get("ProductSecret", None),
                                    data.get("Devicename", None),
                                    data.get("DeviceSecret", None),
                                    data.get("url", None),
                                    int(data.get("qos", 0)),
                                    int(data.get("port", 1883)),
                                    data.get("cleanSession"),
                                    data.get("clientID"),
                                    data.get("publish"),
                                    data.get("subscribe"),
                                    mcu_name=PROJECT_NAME,
                                    mcu_version=PROJECT_VERSION,
                                    firmware_name=DEVICE_FIRMWARE_NAME,
                                    firmware_version=DEVICE_FIRMWARE_VERSION
                                    )
                huawei_iot.init(enforce=True)
                huawei_iot.addObserver(remote_sub)
                remote_pub.add_cloud(huawei_iot, cid)
                self.__channel.cloud_object_dict[cid] = huawei_iot
            elif protocol == "tcp":
                tcp_iot = TcpSocketIot(data.get("url", None),
                                    int(data.get("port")),
                                    reg_data,
                                    data.get("heartbeat"),
                                    data.get("ping"),
                                    data.get("keepAlive"),
                                    )
                tcp_iot.init(enforce=True)
                tcp_iot.start_recv_and_ping()
                tcp_iot.addObserver(remote_sub)
                remote_pub.add_cloud(tcp_iot, cid)
                self.__channel.cloud_object_dict[cid] = tcp_iot
            elif protocol == "udp":
                udp_iot = UdpSocketIot(data.get("url", None),
                                    int(data.get("port")),
                                    reg_data,
                                    data.get("heartbeat"),
                                    data.get("ping"),
                                    data.get("keepAlive"),
                                    )
                udp_iot.init(enforce=True)
                udp_iot.start_recv_and_ping()
                udp_iot.addObserver(remote_sub)
                remote_pub.add_cloud(udp_iot, cid)
                self.__channel.cloud_object_dict[cid] = udp_iot
            elif protocol.startswith("http"):
                http_iot = DtuRequest(data.get("request", None),
                                    data.get("post_data", None),
                                    )
                http_iot.init(enforce=True)
                http_iot.addObserver(remote_sub)
                remote_pub.add_cloud(http_iot, cid)
                self.__channel.cloud_object_dict[cid] = http_iot
            else:
                continue

    def refresh(self):
        log.info("refresh start")
        try:
            _thread.start_new_thread(self.__data_process.read, ())
        except Exception as e:
            pass

    def report_history(self):
        if not self.__history:
            raise TypeError("self.__history is not registered.")
        if not self.__data_process:
            raise TypeError("self.__data_process is not registered.")

        res = True
        hist = self.__history.read()
        print("hist[data]:", hist["data"])

        if hist["data"]:
            pt_count = 0
            for i, data in enumerate(hist["data"]):
                pt_count += 1
                if not self.__data_process.post_history_data(data):
                    res = False
                    break

            hist["data"] = hist["data"][pt_count:]
            if hist["data"]:
                # Flush data in hist-dictionary to tracker_data.hist file.
                self.__history.write(hist["data"])

        return res

def run():
    log.info("PROJECT_NAME: %s, PROJECT_VERSION: %s" % (PROJECT_NAME, PROJECT_VERSION))
    log.info("DEVICE_FIRMWARE_NAME: %s, DEVICE_FIRMWARE_VERSION: %s" % (DEVICE_FIRMWARE_NAME, DEVICE_FIRMWARE_VERSION))

    # 实例化通道数据
    channels = ChannelTransfer(settings.current_settings.get("work_mode"), settings.current_settings.get("conf"))

    if settings.current_settings.get("offline_storage"):
        history = History()

    dtu_gpio_ctrl = Gpio(settings.current_settings.get("pins"))

    through_mode = ThroughMode()

    command_modbus_mode = CommandModbusMode()

    data_process = DtuDataProcess(settings.current_settings)

    data_process.add_module(through_mode)

    data_process.add_module(command_modbus_mode)
    
    data_process.add_module(channels)
    
    remote_sub = RemoteSubscribe()
    remote_sub.add_executor(data_process)

    remote_pub = RemotePublish()
    data_process.add_module(remote_pub)
    if settings.current_settings.get("offline_storage"):
        remote_pub.addObserver(history)

    dtu = Dtu()

    dtu.add_module(dtu_gpio_ctrl)

    dtu.add_module(channels)

    dtu.add_module(data_process)

    dtu.check_sim_status()

    dtu.dialing(settings.current_settings.get("apn"))

    dtu.cloud_init(settings.current_settings.get("conf"), remote_sub, remote_pub)

    if settings.current_settings.get("offline_storage"):
        dtu.add_module(history)
        # 上电之后向云端发送历史数据
        dtu.report_history()
        
    # 上电后立即发送固件版本号
    data_process.ota_check()

    dtu.refresh()


if __name__ == "__main__":
    run()

