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

"""
检查sim卡和网络状态，如有异常尝试CFUN切换或重启
"""
import net
import utime
import _thread
import checkNet
from misc import Power


class NetManager(object):
    RECONNECT_LOCK = _thread.allocate_lock()

    @classmethod
    def reconnect(cls, retry=3):
        with cls.RECONNECT_LOCK:
            for _ in range(retry):
                if cls.wait_connect():
                    return True
                cls.__cfun_switch()
            else:
                Power.powerRestart()
            return False

    @classmethod
    def wait_connect(cls, timeout=30):
        stage, state = checkNet.waitNetworkReady(timeout)
        # print('network status code: {}'.format((stage, state)))
        return stage == 3 and state == 1

    @classmethod
    def __cfun_switch(cls):
        cls.disconnect()
        utime.sleep_ms(200)
        cls.connect()

    @classmethod
    def connect(cls):
        return net.setModemFun(1, 0) == 0

    @classmethod
    def disconnect(cls):
        return net.setModemFun(0, 0) == 0
