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

import request
import ujson

from usr.modules.logging import RET
from usr.modules.logging import error_map
from usr.modules.common import CloudObservable
from usr.modules.logging import getLogger

log = getLogger(__name__)
class DtuRequest(CloudObservable):
    _data_methods = ("PUT", "POST", "DELETE", "HEAD")

    def __init__(self):
        # self.code = code
        self.url = ""
        self.port = ""
        self.method = ""
        self.data = None
        self.serial = 0
        self.channel_id = None
        # 用于识别连接类型
        self.conn_type = "http"

    def serialize(self, data):
        try:
            self.method = data.get("method")
            self.url = data.get("url")
            self.data = data.get("reg_data")
            self.timeout = data.get("reg_datatimeout")
            self.serial = data.get("serialID")
            if self.method.upper() not in ["GET", "POST", "PUT", "DELETE", "HEAD"]:
                return RET.HTTPCHANNELPARSEERR
        except Exception as e:
            return RET.HTTPCHANNELPARSEERR
        else:
            return RET.OK

    # http发送的数据为json类型
    def send(self, data, *args):
        print("send data:", data)
        if isinstance(data, str):
            self.data = data
        else:
            self.data = ujson.dumps(data)
        resp_content = self.req()
        for i in resp_content:
            print(i)

    def req(self):
        global resp
        uri = self.url
        if self.port:
            uri += self.port
        try:
            if self.method.upper() in self._data_methods:
                func = getattr(request, self.method.lower())
                resp = func(uri, data=self.data)
            else:
                resp = request.get(uri, data=self.data)
        except Exception as e:
            # log.info(e)
            log.error("{}: {}".format(error_map.get(RET.HTTPERR), e))
            return RET.HTTPERR
        else:
            if resp.status_code == 302:
                log.error(error_map.get(RET.REQERR1))
            if resp.status_code == 404:
                log.error(error_map.get(RET.REQERR2))
            if resp.status_code == 500:
                log.error(error_map.get(RET.REQERR))
            if resp.status_code == 200:
                print("HTTP RESP")
                print(resp)
                # TODO HTTP data Parse func
                #rec = self.uart.output(resp.status_code, self.serial, request_id=self.channel_id)
                #if isinstance(rec, dict):
                 #   self.send(rec)
            return resp.content

    def check_net(self):
        resp = request.get(self.url)
        return resp.status_code