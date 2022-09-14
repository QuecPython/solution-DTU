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
@file      :huawei_cloud.py
@author    :elian.wang@quectel.com
@brief     :This file shows the interface of Huawei cloud
@version   :0.1
@date      :2022-05-18 09:14:22
@copyright :Copyright (c) 2022
"""


import ujson
import utime
import _thread
import ubinascii
import uhashlib


from umqtt import MQTTClient
from usr.modules.logging import getLogger
from usr.modules.common import CloudObservable
log = getLogger(__name__)


class HuaweiIot(CloudObservable):
    """This is a class for huaweiyun iot.

    This class extend CloudObservable.

    This class has the following functions:
        1. Cloud connect and disconnect
        2. Publish data to cloud
        3. Subscribe data from cloud

    Attribute:
        pub_topic_dict: topic dict for publish dtu through data
        sub_topic_dict: topic dict for subscribe cloud through data
        conn_type:cloud name

    Run step:
        1. cloud = HuaweiIot(pk, ps, dk, ds, server, qos, port, clean_session, client_id, pub_topic, sub_topic)
        2. cloud.addObserver(RemoteSubscribe)
        3. cloud.init()
        4. cloud.post_data(data)
        5. cloud.close()
    """
    def __init__(self, pk, ps, dk, ds, server, qos, port, clean_session, client_id, pub_topic=None, sub_topic=None, life_time=120,
                 mcu_name="", mcu_version="", firmware_name="", firmware_version="", reconn=True):
        """
        1. Init parent class CloudObservable
        2. Init cloud connect params and topic
        """
        super().__init__()
        self.conn_type = "hwyun"
        self.__pk = pk
        self.__ps = ps
        self.__dk = dk
        self.__ds = ds
        self.__server = server
        self.__qos = qos
        self.__port = port
        self.__huaweiyun = None
        self.__clean_session = clean_session
        self.__life_time = life_time
        self.__mcu_name = mcu_name
        self.__mcu_version = mcu_version
        self.__firmware_name = firmware_name
        self.__firmware_version = firmware_version
        self.__reconn = reconn
        self.__object_model = None
        self.__client_id = client_id
        self.__post_res = {}
        self.__password = None

        if pub_topic == None:
            self.pub_topic_dict = {"0": "$oc/devices/%s/sys/messages/up" % (self.__dk)}
        else:
            self.pub_topic_dict = pub_topic
        if sub_topic == None:
            self.sub_topic_dict = {"0": "$oc/devices/%s/sys/messages/down" % (self.__dk)}
        else:
            self.sub_topic_dict = sub_topic

    def __huaweiyun_subscribe_topic(self):
        for id, usr_sub_topic in self.sub_topic_dict.items():
            if self.__huaweiyun.subscribe(usr_sub_topic, qos=0) == -1:
                log.error("Topic [%s] Subscribe Falied." % usr_sub_topic)


    def __huaweiyun_sub_cb(self, topic, data):
        """Huaweiyun subscribe topic callback

        Parameter:
            topic: topic info
            data: response dictionary info
        """
        topic = topic.decode()
        try:
            data = ujson.loads(data)
            data = data["content"]
        except:
            pass

        try:
            self.notifyObservers(self, *("raw_data", {"topic":topic, "data":data} ) )
        except Exception as e:
            log.error("{}".format(e))

    def __listen(self):
        while True:
            self.__huaweiyun.wait_msg()
            utime.sleep_ms(100)

    def __start_listen(self):
        """Start a new thread to listen to the cloud publish 
        """
        _thread.start_new_thread(self.__listen, ())

    @staticmethod
    def __hmac_sha256_digest(key_K, data):
        """huwei iot generate password

        Args:
            key_K (_type_): time sign
            data (_type_): device secret
        """
        def xor(x, y):
            return bytes(x[i] ^ y[i] for i in range(min(len(x), len(y))))

        if len(key_K) > 64:
            raise ValueError("The key must be <= 64 bytes in length")
        padded_K = key_K + b"\x00" * (64 - len(key_K))
        ipad = b"\x36" * 64
        opad = b"\x5c" * 64
        h_inner = uhashlib.sha256(xor(padded_K, ipad))
        h_inner.update(data)
        h_outer = uhashlib.sha256(xor(padded_K, opad))
        h_outer.update(h_inner.digest())
        return ubinascii.hexlify(h_outer.digest()).decode()

    def init(self, enforce=False):
        """Huweiyun connect and subscribe topic

        Parameter:
            enforce:
                True: enfore cloud connect and subscribe topic
                False: check connect status, return True if cloud connected

        Return:
            Ture: Success
            False: Failed
        """
        log.debug("[init start] enforce: %s" % enforce)
        if enforce is False and self.__huaweiyun is not None:
            log.debug("self.get_status(): %s" % self.get_status())
            if self.get_status():
                return True

        if self.__huaweiyun is not None:
            self.close()
        
        local_time = utime.localtime()
        time_sign = "%s%s%s%s" % (local_time[0], "%02d" % local_time[1], "%02d" % local_time[2], "%02d" % local_time[3])
        self.__client_id = self.__dk + "_0_0_" + time_sign
        self.__password = self.__hmac_sha256_digest(time_sign.encode("utf-8"), self.__ds.encode("utf-8"))

        log.debug("HuaweiYun init. self.__client_id: %s, self.__password: %s, self.__dk: %s, self.__ds: %s" % (self.__client_id, self.__password, self.__dk, self.__ds))
        self.__huaweiyun = MQTTClient(client_id=self.__client_id, server=self.__server, port=self.__port,
                              user=self.__dk, password=self.__password, keepalive=self.__life_time, ssl=False)
        try:
            self.__huaweiyun.connect(clean_session=self.__clean_session)
        except Exception as e:
            log.error("HuaweiYun connect error: %s" % e)
        else:
            self.__huaweiyun.set_callback(self.__huaweiyun_sub_cb)
            self.__huaweiyun_subscribe_topic()
            log.debug("HuaweiYun __huaweiyun_subscribe_topic")
            self.__start_listen()
            log.debug("HuaweiYun start.")

        log.debug("self.get_status(): %s" % self.get_status())
        if self.get_status():
            return True
        else:
            return False

    def close(self):
        self.__huaweiyun.disconnect()

    def get_status(self):
        """Get huaweiyun connect status

        Return:
            True -- connect success
            False -- connect falied
        """
        try:
            return True if self.__huaweiyun.get_mqttsta() == 0 else False
        except:
            return False
    
    def through_post_data(self, data, topic_id):
        try:
            self.__huaweiyun.publish(self.pub_topic_dict[topic_id], data, self.__qos)
        except Exception:
            log.error("Huaweiyun publish topic %s failed. data: %s" % (self.pub_topic_dict[topic_id], data))
            return False
        else:
            return True

    def post_data(self, data):
        pass

    def ota_request(self):
        pass

    def ota_action(self, action, module=None):
        pass
    
    def device_report(self):
        pass