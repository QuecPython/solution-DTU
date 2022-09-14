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
@file      :requestIot.py
@author    :elian.wang@quectel.com
@brief     :cloud that communicate using HTTP,Dtu communicate interface
@version   :0.1
@date      :2022-05-19 10:49:01
@copyright :Copyright (c) 2022
"""

import ujson
import request

from usr.modules.common import CloudObservable
from usr.modules.logging import getLogger

log = getLogger(__name__)
class DtuRequest(CloudObservable):
    """This is a class for http iot.

    This class extend CloudObservable.

    This class has the following functions:
        1. send data to http server
        2. parse http server ack data

    Attribute:
        conn_type:cloud name

    Run step:
        1. cloud = DtuRequest(request_id_dict, reg_data)
        2. cloud.addObserver(RemoteSubscribe)
        3. cloud.init()
        4. cloud.through_post_data(data)
    """
    def __init__(self, request_id_dict, post_data=""):
        super().__init__()
        self.conn_type = "http"
        self.__post_data = post_data
        self.__request_id_dict = request_id_dict
        self.__url = None
        self.__method = None
        self.__data_methods = ("PUT", "POST", "DELETE", "HEAD", "GET")
        try:
            for k,v in self.__request_id_dict.items():
                if v.get("method").upper() in self.__data_methods:
                    self.__method = v.get("method").upper()
                    self.__url = v.get("url")
                else:
                    raise Exception("http param error")
        except Exception as e:
            log.error("request id dict error:", e)
    
    def init(self,  enforce=False):
        return True

    def __req(self, data, request_id):
        global resp
        print("url", self.__url)
        print("method", self.__method)
        uri = self.__url
        try:
            if self.__method in self.__data_methods:
                func = getattr(request, self.__method.lower())
                resp = func(uri, data=data)
            else:
                resp = request.get(uri, data=data)
        except Exception as e:
            log.error("http request error: {}".format(e))
            return False
        else:
            try:
                read_data = ""
                for i in resp.content:
                    read_data += i
            except Exception as e:
                log.error("resp.content fault:", e)
                return False
            if resp.status_code == 200:
                try:
                    self.notifyObservers(self, *("raw_data", {"request_id":request_id, "data":read_data}))
                except Exception as e:
                    log.error("{}".format(e))
                    return False
                return True
            else:
                log.error("http error:", resp.status_code)
                return False

        
    # http发送的数据为json类型
    def through_post_data(self, data, request_id):
        if isinstance(data, str):
            data = data
        else:
            data = ujson.dumps(data)
        try:
            for k,v in self.__request_id_dict.items():
                if k == request_id:
                    self.__method = v.get("method").upper()
                    self.__url = v.get("url")
        except Exception as e:
            log.error("request id dict error:", e)
            return False
        return self.__req(data, request_id)
    
    def get_status(self):
        resp = request.get(self.__url)
        if resp.status_code == 200:
            return True 
        else:
            return False

    def post_data(self, data):
        pass

    def ota_request(self):
        pass

    def ota_action(self, action, module=None):
        pass

    def device_report(self):
        pass