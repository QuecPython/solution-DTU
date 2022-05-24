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

import request
import ujson

from usr.modules.logging import RET
from usr.modules.logging import error_map
from usr.modules.common import CloudObservable
from usr.modules.logging import getLogger

log = getLogger(__name__)
class DtuRequest(CloudObservable):

    def __init__(self, request_id_dict, reg_data="", timeout=120):
        self.conn_type = "http"
        self.__reg_data = reg_data
        self.__timeout = timeout
        self.__request_id_dict = request_id_dict
        self.__url = None
        self.__method = None
        self.__data_methods = ("PUT", "POST", "DELETE", "HEAD")
        try:
            for k,v in self.__request_id_dict.items():
                if v.get("method").upper() in ["GET", "POST", "PUT", "DELETE", "HEAD"]:
                    self.__method = v.get("method").upper()
                    self.__url = v.get("url").upper()
                else:
                    return RET.HTTPCHANNELPARSEERR
        except Exception as e:
            log.error("request id dict error:", e)
    
    def init(self,  enforce=False):
        return True

    def __req(self, data):
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
            log.error("{}: {}".format(error_map.get(RET.HTTPERR), e))
            return False
        else:
            if resp.status_code == 302:
                log.error(error_map.get(RET.REQERR1))
                return False
            if resp.status_code == 404:
                log.error(error_map.get(RET.REQERR2))
                return False
            if resp.status_code == 500:
                log.error(error_map.get(RET.REQERR))
                return False
            if resp.status_code == 200:
                print("HTTP RESP")
                print(resp)
                try:
                    self.notifyObservers(self, *("raw_data", {"request":"0", "data":data}))
                except Exception as e:
                    log.error("{}".format(e))
                return True

        
    # http发送的数据为json类型
    def send(self, data, request_id):
        print("send data:", data)
        print("request_id:", request_id)
        if isinstance(data, str):
            data = data
        else:
            data = ujson.dumps(data)
        try:
            for k,v in self.__request_id_dict.items():
                if k == request_id:
                    self.__method = v.get("method").upper()
                    self.__url = v.get("url").upper()
        except Exception as e:
            log.error("request id dict error:", e)
        return self.__req(data)
    
    def get_status(self):
        resp = request.get(self.__url)
        if resp.status_code == 200:
            return True 
        else:
            return False