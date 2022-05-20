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
@file      :logging.py
@author    :elian.wang@quectel.com
@brief     :print debug、error message
@version   :0.1
@date      :2022-05-20 16:26:41
@copyright :Copyright (c) 2022
"""



import utime


# 新增系统日志上报功能
class RET:
    OK = "20000"
    HTTP_OK = "20001"
    MQTT_OK = "20002"
    SOCKET_TCP_OK = "20003"
    SOCKET_UDP_OK = "20004"
    Aliyun_OK = "20005"
    TXyun_OK = "20006"
    # 系统组件错误
    SIMERR = "3001"
    DIALINGERR = "3002"
    # 网络协议错误
    HTTPERR = "4001"
    REQERR = "4002"
    TCPERR = "4003"
    UDPERR = "4004"
    MQTTERR = "4005"
    ALIYUNMQTTERR = "4006"
    TXYUNMQTTERR = "4007"
    PROTOCOLERR = "4008"
    REQERR1 = "4009"
    QUECIOTERR = "4010"
    HWYUNERR = "4011"
    REQERR2 = "5000"
    # 功能错误
    PASSWORDERR = "5001"
    PASSWDVERIFYERR = "5002"
    HTTPCHANNELPARSEERR = "5003"
    CHANNELERR = "5004"
    DATATYPEERR = "5005"
    METHODERR = "5006"
    DATASENDERR = "5007"
    IOTTYPERR = "5008"
    NUMBERERR = "5009"
    MODBUSERR = "5010"
    # 解析错误
    JSONLOADERR = "6001"
    JSONPARSEERR = "6002"
    PARSEERR = "6003"
    DATAPARSEERR = "6004"
    POINTERR = "6005"
    READFILEERR = "6006"
    CONFIGNOTEXIST = "6007"
    # 提醒
    CMDPARSEERR = "7001"


error_map = {
    RET.OK: u"成功",
    RET.HTTP_OK: u"http connect success",
    RET.MQTT_OK: u"mqtt connect success",
    RET.SOCKET_TCP_OK: u"tcp connect success",
    RET.SOCKET_UDP_OK: u"udp connect success",
    RET.Aliyun_OK: u"aliyun connect success",
    RET.TXyun_OK: u"txyun connect success",
    # 系统
    RET.SIMERR: u"read sim card error",
    RET.DIALINGERR: u"dialing error",
    # 协议
    RET.HTTPERR: u"http request error",
    RET.REQERR: u"http request 500",
    RET.REQERR1: u"http request 302",
    RET.REQERR2: u"http request 404",
    RET.TCPERR: u"tcp connect failed",
    RET.UDPERR: u"udp connect failed",
    RET.MQTTERR: u"mqtt connect failed",
    RET.ALIYUNMQTTERR: u"aliyun connect failed",
    RET.TXYUNMQTTERR: u"txyun connect failed",
    RET.PROTOCOLERR: u"protocol parse error",
    RET.QUECIOTERR: u"quecthing connect failed",
    RET.HWYUNERR: u"huaweiyun connect failed",
    # 功能错误
    RET.PASSWORDERR: u"password not found",
    RET.PASSWDVERIFYERR: u"password verify error",
    RET.HTTPCHANNELPARSEERR: u"http param error",
    RET.CHANNELERR: u"through channel error",
    RET.DATATYPEERR: u"data type error",
    RET.METHODERR: u"method error",
    RET.DATASENDERR: u"through data send error",
    RET.IOTTYPERR: u"mqtt type error",
    RET.NUMBERERR: u"params number error",
    RET.MODBUSERR: u"modbus prase error",
    # 数据错误
    RET.JSONLOADERR: "json load err",
    RET.JSONPARSEERR: "json parse err",
    RET.PARSEERR: "parse error",
    RET.DATAPARSEERR: "data parse error",
    RET.POINTERR: "command code error",
    RET.READFILEERR: "read file error",
    # 提醒
    RET.CMDPARSEERR: "command parse error transfer to modbus"
}

class DTUException(Exception):
    def __init__(self, message):
        self.message = message

class Logger:
    def __init__(self, name):
        self.name = name
        self.__debug = True
        self.__level = "debug"
        self.__level_code = {
            "debug": 0,
            "info": 1,
            "warn": 2,
            "error": 3,
            "critical": 4,
        }

    def get_debug(self):
        return self.__debug

    def set_debug(self, debug):
        if isinstance(debug, bool):
            self.__debug = debug
            return True
        return False

    def get_level(self):
        return self.__level

    def set_level(self, level):
        if self.__level_code.get(level) is not None:
            self.__level = level
            return True
        return False

    def log(self, name, level, *message):
        if self.__debug is False:
            if self.__level_code.get(level) < self.__level_code.get(self.__level):
                return

        if hasattr(utime, "strftime"):
            print(
                "[{}]".format(utime.strftime("%Y-%m-%d %H:%M:%S")),
                "[{}]".format(name),
                "[{}]".format(level),
                *message
            )
        else:
            t = utime.localtime()
            print(
                "[{}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}]".format(*t),
                "[{}]".format(name),
                "[{}]".format(level),
                *message
            )

    def critical(self, *message):
        self.log(self.name, "critical", *message)

    def error(self, *message):
        self.log(self.name, "error", *message)

    def warn(self, *message):
        self.log(self.name, "warn", *message)

    def info(self, *message):
        self.log(self.name, "info", *message)

    def debug(self, *message):
        self.log(self.name, "debug", *message)


def getLogger(name):
    return Logger(name)
