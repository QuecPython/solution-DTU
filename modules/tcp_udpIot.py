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
@file      :tcp_udpIot.py
@author    :elian.wang
@brief     :tcp、upp iot interface
@version   :0.1
@date      :2022-05-18 11:54:10
@copyright :Copyright (c) 2022
"""

import usocket
import utime
import ujson

from usr.modules.logging import RET
from usr.modules.logging import error_map
from usr.modules.logging import getLogger
from usr.modules.common import CloudObservable

log = getLogger(__name__)

class SocketIot(CloudObservable):
    """This is a class for tcp udp iot

    Args:
        object (_type_): _description_
    """
    def __init__(self, server, port, heartbeat_time, ping="", life_time=120):
        self.__cli = None
        self.__server = server
        self.__port = port
        self.__life_time = life_time
        self.__ping = ping
        self.__heartbeat_time = heartbeat_time
        self.conn_type = "socket"

    def __first_reg(self, reg_data):  # 发送注册信息
        try:
            self.__cli.send(str(reg_data).encode("utf-8"))
            # log.info("Send first login information {}".format(reg_data))
        except Exception as e:
            log.info("send first login information failed !{}".format(e))

    def init(self, enforce=False):
        sock_addr = usocket.getaddrinfo(self.url, int(self.port))[0][-1]
        log.info("sock_addr = {}".format(sock_addr))
        self.__cli.connect(sock_addr)
        self.__first_reg()

    def send(self, data, *args):
        try:
            print("send data:", data)
            if isinstance(data, str):
                send_data = data
            else:
                send_data = ujson.dumps(data)
            self.__cli.send(send_data.encode("utf-8"))
        except Exception as e:
            log.error("{}: {}".format(error_map.get(RET.DATAPARSEERR), e))

    def recv(self):
        while True:
            try:
                data = self.__cli.recv(1024)
            except Exception as e:
                print(e)
                utime.sleep_ms(50)
                continue
            else:
                if data != b"":
                    print("socket data:", data)
                    
                    rec = self.dtu_uart.output(data.decode(), self.serial, request_id=self.channel_id)
                    if isinstance(rec, dict):
                        self.send(rec)
                    
                else:
                    utime.sleep_ms(50)
                    continue

    def heartbeat(self):  # 发送心跳包
        while True:
            log.info("send heartbeats")
            try:
                self.__cli.send(self.ping.encode("utf-8"))
                log.info("Send a heartbeat: {}".format(self.ping))
            except Exception as e:
                log.info("send heartbeat failed !")
            print("heart time", self.heart)
            utime.sleep(self.heart)

    

    def close(self):
        self.__cli.close()

    def get_status(self):
        return self.__cli.getsocketsta()


class TcpSocket(DtuSocket):

    def __init__(self):
        super(TcpSocket, self).__init__()
        # self.code = code
        self.cli = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
        self.cli.settimeout(self.keep_alive)  # 链接超时最大时间
        self.conn_type = "tcp"


class UdpSocket(DtuSocket):

    def __init__(self):
        super(UdpSocket, self).__init__()
        # self.code = code
        self.cli = usocket.socket(usocket.AF_INET, usocket.SOCK_DGRAM)
        self.cli.settimeout(self.keep_alive)
        self.conn_type = "udp"
