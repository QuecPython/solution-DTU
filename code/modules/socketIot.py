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
@file      :tcp.py
@author    :Elian.wang (elian.wang@quectel.com)
@version   :1.0.0
@date      :2022-08-05 10:48:43
@copyright :Copyright (c) 2022
"""
import usys
import utime
import _thread
import usocket
from usr.modules.logging import getLogger
from usr.modules.common import CloudObservable
from usr.modules.common import option_lock, Singleton

logger = getLogger(__name__)

_socket_lock = _thread.allocate_lock()

class Socket(CloudObservable):
    """This class is tcp socket"""

    def __init__(self, ip_type=None, protocol = "TCP", keep_alive=None, domain=None, port=None):
        super().__init__()
        if protocol == "TCP" or protocol == None:
            self.__protocol = "TCP"
        else:
            self.__protocol = "UDP"
        if ip_type == "IPv6":
            self.__ip_type = usocket.AF_INET6
        else:
            self.__ip_type = usocket.AF_INET
        self.__port = port
        self.__domain = domain
        self.__addr = None
        self.__socket = None
        self.__socket_args = []
        self.__timeout = 50
        self.__keep_alive = keep_alive
        self.__listen_thread_id = None
        self.__init_addr()
        self.__init_socket()
        
    def __init_addr(self):
        """Get ip and port from domain.

        Raises:
            ValueError: Domain DNS parsing falied.
        """
        if self.__domain is not None:
            if self.__port is None:
                self.__port == 8883 if self.__domain.startswith("https://") else 1883
            try:
                addr_info = usocket.getaddrinfo(self.__domain, self.__port)
                self.__ip = addr_info[0][-1][0]
            except Exception as e:
                usys.print_exception(e)
                raise ValueError("Domain %s DNS parsing error. %s" % (self.__domain, str(e)))
        self.__addr = (self.__ip, self.__port)

    def __init_socket(self):
        """Init socket by ip, port and method

        Raises:
            ValueError: ip or domain or method is illegal.
        """
        if self.__protocol == 'TCP':
            socket_type = usocket.SOCK_STREAM
            socket_proto = usocket.IPPROTO_TCP
        elif self.__protocol == 'UDP':
            socket_type = usocket.SOCK_DGRAM
            socket_proto = usocket.IPPROTO_UDP
        else:
            raise ValueError("Args method is TCP or UDP, not %s" % self.__protocol)
        self.__socket_args = (self.__ip_type, socket_type, socket_proto)

    @option_lock(_socket_lock)
    def __connect(self):
        """Socket connect when method is TCP

        Returns:
            bool: True - success, False - falied
        """
        if self.__socket_args:
            try:
                self.__socket = usocket.socket(*self.__socket_args)
                if self.__protocol == "TCP":
                    self.__socket.connect(self.__addr)
                return True
            except Exception as e:
                usys.print_exception(e)

        return False

    @option_lock(_socket_lock)
    def __disconnect(self):
        """Socket disconnect

        Returns:
            bool: True - success, False - falied
        """
        if self.__socket is not None:
            try:
                self.__socket.close()
                self.__socket = None
                return True
            except Exception as e:
                usys.print_exception(e)
                return False
        else:
            return True

    def __recv(self):
        """Read data by socket.
        """
        while True:
            data = b""
            try:
                if self.__socket is not None:
                    data = self.__socket.recv(1024)
            except Exception as e:
                if e.args[0] != 110:
                    logger.error("%s read falied. error: %s" % (self.__protocol, str(e)))
                    break
            else:
                if data != b"":
                    try:
                        self.notifyObservers(self, *("raw_data", {"topic":None, "data":data} ) )
                    except Exception as e:
                        logger.error("{}".format(e))
            utime.sleep_ms(50)

    @option_lock(_socket_lock)
    def __send(self, data):
        """Send data by socket.

        Args:
            data(str): To be send data

        Returns:
            bool: True - success, False - falied.
        """
        if self.__socket is not None:
            try:
                write_data_num = self.__socket.write(data)
                if write_data_num == len(data):
                    return True
            except Exception as e:
                usys.print_exception(e)

        return False
    
    def __listen(self):
        self.__listen_thread_id = _thread.start_new_thread(self.__recv, ())

    def init(self, enforce=False):
        """Socket connect and register receive thread

        Args:
            enforce (bool, optional): Whether to force initialization. Defaults to False.

        Returns:
            bool: True - success, False - falied.
        """
        if enforce is False:
            if self.get_status() == 0:
                return True
        if self.__socket is not None:
            try:
                self.__disconnect()
            except Exception as e:
                logger.error("tcp disconnect falied. %s" % e)
            try:
                if self.__listen_thread_id is not None:
                    _thread.stop_thread(self.__listen_thread_id)
            except Exception as e:
                logger.error("stop listen thread falied. %s" % e)

        # FIX: when connect failed we return False instead of raise Exception for another try(self.init when post data.)
        if not self.__connect():
            return False

        if self.__keep_alive != 0:
            try:
                self.__socket.setsockopt(usocket.SOL_SOCKET, usocket.TCP_KEEPALIVE, self.__keep_alive)
            except Exception as e:
                self.__socket.close()
                logger.error("socket option set error:", e)
                raise Exception("socket option set error")
        self.__socket.settimeout(self.__timeout)
        # Start receive socket data
        self.__listen()
        logger.debug("self.get_status(): %s" % self.get_status())
        if self.get_status() == 0:
            return True
        else:
            return False

    def get_status(self):
        """Get socket connection status

        Returns:
            [int]:
                -1: Error
                 0: Connected
                 1: Connecting
                 2: Disconnect
        """
        _status = -1
        if self.__socket is not None:
            try:
                if self.__protocol == "TCP":
                    socket_sta = self.__socket.getsocketsta()
                    if socket_sta in range(4):
                        # Connecting
                        _status = 1
                    elif socket_sta == 4:
                        # Connected
                        _status = 0
                    elif socket_sta in range(5, 11):
                        # Disconnect
                        _status = 2
                elif self.__protocol == "UDP":
                    _status = 0
            except Exception as e:
                usys.print_exception(e)
        return _status

    def through_post_data(self, data, topic_id):
        return self.__send(data)

    def post_data(self, data):
        pass

    def ota_request(self):
        pass

    def ota_action(self, action, module=None):
        pass

    def device_report(self):
        pass

