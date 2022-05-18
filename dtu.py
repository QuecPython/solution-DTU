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
@author    :elian.wang
@brief     :dtu main function
@version   :0.1
@date      :2022-05-18 09:12:37
@copyright :Copyright (c) 2022
"""

import sim, uos, dataCall, ujson, net, modem, utime, _thread, uhashlib, fota, ure, ubinascii, cellLocator, request
from usr.modules.common import Singleton
from usr.modules.aliyunIot import AliYunIot, AliObjectModel
from usr.modules.quecthing import QuecThing, QuecObjectModel
from usr.modules.mqttIot import MqttIot
from usr.modules.huawei_cloud import HuaweiIot
from usr.modules.txyunIot import TXYunIot
from usr.modules.requestIot import DtuRequest
from usr.modules.tcp_udpIot import TcpSocket
from usr.modules.tcp_udpIot import UdpSocket

from usr.dtu_data_process import DtuDataProcess
from usr.dtu_channels import ChannelTransfer
from usr.modules.logging import RET
from usr.modules.logging import error_map
from usr.dtu_gpio import ProdGPIO
from usr.modules.remote import RemotePublish, RemoteSubscribe
from usr.modules.logging import getLogger
from usr.settings import PROJECT_NAME, PROJECT_VERSION, DEVICE_FIRMWARE_NAME, DEVICE_FIRMWARE_VERSION
from usr.dtu_protocol_data import DtuProtocolData
from usr.modules.history import History
from usr.settings import settings

log = getLogger(__name__)


class Dtu(Singleton):

    def __init__(self):
        self.__gpio = None
        self.__data_process = None
        self.__channel = None
        self.__history = None

    def add_module(self, module):
        if isinstance(module, ProdGPIO):
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


    def prepare(self):
        while True:
            if not sim.getStatus():
                if not self.__gpio.status():
                    self.__gpio.show()
                utime.sleep(1)
            else:
                break

    def dialing(self, apn):
        # 文件备份
        call_count = 0
        if apn[0] != "" and apn[1] != "" and apn[2] != "":
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

        # 检查拨号结果，拨号失败闪烁LED灯
        self.__gpio.LED_blink(dataCall.getInfo(1, 0)[2][0], 10)

    def data_info(self, version, imei, code, msg):
        data = {
            "version": version,
            "ver": "v1.0",
            "imei": imei,
            "code": code,
            "msg": msg
        }
        return data

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
                                    int(data.get("cleanSession"),0),
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
                tcp_sock = TcpSocket(self.__data_process)
                status = tcp_sock.serialize(data)
                try:
                    tcp_sock.connect()
                    _thread.start_new_thread(tcp_sock.recv, ())
                except Exception as e:
                    log.error("{}: {}".format(error_map.get(RET.TCPERR), e))
                else:
                    if status == RET.OK:
                        if self.__parse_data.reg == 1:
                            tcp_sock.first_reg(reg_data)
                            log.info("TCP send first login information {}".format(reg_data))
                        if data.get("ping"):
                            if int(data.get("heartbeat")) != 0:
                                _thread.start_new_thread(tcp_sock.Heartbeat, ())
                        self.__channel.cloud_object_dict[cid] = tcp_sock
                        tcp_sock.channel_id = cid
                    else:
                        log.error(error_map.get(RET.TCPERR))

            elif protocol == "udp":
                udp_sock = UdpSocket()
                status = udp_sock.serialize(data)
                try:
                    udp_sock.connect(self.__data_process)
                    _thread.start_new_thread(udp_sock.recv, ())
                except Exception as e:
                    log.error("{}: {}".format(error_map.get(RET.UDPERR), e))
                else:
                    if status == RET.OK:
                        if self.__parse_data.reg == 1:
                            udp_sock.first_reg(reg_data)
                            log.info("UDP send first login information {}".format(reg_data))
                        if data.get("ping"):
                            if int(data.get("heartbeat")) != 0:
                                _thread.start_new_thread(udp_sock.Heartbeat, ())
                        self.__channel.cloud_object_dict[cid] = udp_sock
                        udp_sock.channel_id = cid
                    else:
                        log.error(error_map.get(RET.UDPERR))

            elif protocol.startswith("http"):
                dtu_req = DtuRequest()
                dtu_req.addObserver(self.__remote_sub)
                
                status = dtu_req.serialize(data)
                if status == RET.OK:
                    data = dtu_req.req()  # 发送请求
                    print("***********************http request***********************")
                    for i in data:
                        print(i)
                    self.__channel.cloud_object_dict[cid] = dtu_req
                    dtu_req.channel_id = cid
                else:
                    log.error(error_map.get(RET.HTTPERR))
            else:
                continue

    def refresh(self):
        log.info("refresh start")
        # TODO 判断 auto_connect 
        try:
            self.prepare()
            log.info("prepart ready")

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

    # 实例化DTU协议数据解析方法
    dtu_protocol_data = DtuProtocolData()

    if settings.current_settings.get("offline_storage"):
        history = History()

    data_process = DtuDataProcess(settings.current_settings)

    data_process.set_channel(channels)

    data_process.set_procotol_data(dtu_protocol_data)
    
    remote_sub = RemoteSubscribe()
    remote_sub.add_executor(data_process)

    remote_pub = RemotePublish()
    data_process.add_module(remote_pub)
    if settings.current_settings.get("offline_storage"):
        remote_pub.addObserver(history)

    dtu = Dtu()

    dtu.add_module(ProdGPIO(settings.current_settings.get("pins")))

    dtu.add_module(channels)

    dtu.add_module(data_process)

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

