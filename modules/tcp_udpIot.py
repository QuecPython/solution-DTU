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
@author    :elian.wang@quectel.com
@brief     :tcp、upp iot interface
@version   :0.1
@date      :2022-05-18 11:54:10
@copyright :Copyright (c) 2022
"""


import utime
import ujson
import _thread
import usocket

from usr.modules.logging import getLogger
from usr.modules.common import CloudObservable

log = getLogger(__name__)

class SocketIot(CloudObservable):
    """This is a class for tcp udp iot
    """
    def __init__(self, server, port, reg_data, keepalive_interval, ping=""):
        super().__init__()
        self.__cli = None
        self.__server = server
        self.__port = port
        self.__reg_data = reg_data
        self.__ping = ping
        self.__keepalive_interval = keepalive_interval
        self.cloud_name = "socket"

    def __first_reg(self):
        """Send registration Information
        """
        try:
            self.__cli.send(str(self.__reg_data).encode("utf-8"))
        except Exception as e:
            log.info("send first login information failed !{}".format(e))

    def init(self, enforce=False):
        pass

    def __recv(self):
        while True:
            try:
                data = self.__cli.recv(1024)
            except Exception as e:
                log.info("recv error:", e)
                utime.sleep_ms(50)
                continue
            else:
                if data != b"":
                    try:
                        self.notifyObservers(self, *("raw_data", {"topic":None, "data":data} ) )
                    except Exception as e:
                        log.error("{}".format(e))
                else:
                    utime.sleep_ms(50)
                    continue

    def __heartbeat(self):
        while True:
            log.info("send heartbeats")
            try:
                self.__cli.send(self.__ping.encode("utf-8"))
                log.info("Send a heartbeat: {}".format(self.__ping))
            except Exception as e:
                log.info("send heartbeat failed !")
            utime.sleep(self.__keepalive_interval)

    def __send(self, data):
        try:
            if isinstance(data, str):
                send_data = data
            elif isinstance(data, dict):
                send_data = ujson.dumps(data)
            else:
                send_data = str(data)
            res = self.__cli.send(send_data.encode("utf-8"))
            if res > 0:
                return True
            else:
                return False
        except Exception as e:
            log.error("data parse error: {}".format(e))
            return False
    
    def through_post_data(self, data, topic_id):
        return self.__send(data)

    def close(self):
        try:
            self.__cli.close()
        except Exception as e:
            log.error("SocketIot close err:", e)

    def get_status(self):
        """Get mqtt connect status

        Return:
            True -- connect success
            False -- connect falied
        """
        try:
            return True if self.__cli.getsocketsta() > 0 else False
        except:
            return False
            
    def start_recv_and_ping(self):
        # if ping and heartbeat time configed,call heartbeat
        if self.__keepalive_interval != 0 and self.__ping is not "":
            _thread.start_new_thread(self.__heartbeat, ())
        # call receive socket data
        _thread.start_new_thread(self.__recv, ())

    def post_data(self, data):
        pass

    def ota_request(self):
        pass

    def ota_action(self, action, module=None):
        pass

    def device_report(self):
        pass


class TcpSocketIot(SocketIot):
    """TCP Communication type Iot
    """
    def __init__(self, server, port, reg_data, keepalive_interval, ping="", life_time=120):
        super().__init__(server, port, reg_data, keepalive_interval, ping=ping)
        self.__life_time = life_time
        self.cloud_name = "tcp"
        
    def init(self, enforce=False):
        log.debug("[init start] enforce: %s" % enforce)
        if enforce is False and self.__cli is not None:
            log.debug("self.get_status(): %s" % self.get_status())
            if self.get_status():
                return True

        if self.__cli is not None:
            self.close()

        sock_addr = usocket.getaddrinfo(self.__server, int(self.__port))[0][-1]
        log.info("sock_addr = {}".format(sock_addr))
        self.__cli = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
        self.__cli.settimeout(self.__life_time)
        self.__cli.connect(sock_addr)
        self.__first_reg()


class UdpSocketIot(SocketIot):
    """UDP Communication type Iot
    """
    def __init__(self, server, port, reg_data, keepalive_interval, ping="", life_time=120):
        super().__init__(server, port, reg_data, keepalive_interval, ping=ping)
        self.__life_time = life_time
        self.cloud_name = "udp"
    
    def init(self, enforce=False):
        log.debug("[init start] enforce: %s" % enforce)
        if enforce is False and self.__cli is not None:
            log.debug("self.get_status(): %s" % self.get_status())
            if self.get_status():
                return True

        if self.__cli is not None:
            self.close()

        sock_addr = usocket.getaddrinfo(self.__server, int(self.__port))[0][-1]
        log.info("sock_addr = {}".format(sock_addr))
        self.__cli = usocket.socket(usocket.AF_INET, usocket.SOCK_DGRAM)
        self.__cli.settimeout(self.__life_time)
        self.__cli.connect(sock_addr)
        self.__first_reg()

    def get_status(self):
        return True

    def close(self):
        pass
    
