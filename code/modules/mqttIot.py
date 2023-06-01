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
@file      :mqttIot.py
@author    :elian.wang@quectel.com
@brief     :universal mqtt iot inferface
@version   :0.1
@date      :2022-05-18 13:28:53
@copyright :Copyright (c) 2022
"""

import ujson
import utime
import _thread
from umqtt import MQTTClient
from usr.modules.logging import getLogger
from usr.modules.common import CloudObservable
log = getLogger(__name__)

class MqttIot(CloudObservable):
    """This is a class for universal mqtt iot.

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
        1. cloud = MqttIot(server, qos, port, clean_session, client_id, pub_topic, sub_topic)
        2. cloud.addObserver(RemoteSubscribe)
        3. cloud.init()
        4. cloud.post_data(data)
        5. cloud.close()
    """
    def __init__(self, server, qos, port, clean_session, client_id, user, pass_word, pub_topic=None, sub_topic=None, life_time=120):
        """
        1. Init parent class CloudObservable
        2. Init cloud connect params and topic
        """
        super().__init__()
        self.conn_type = "mqtt"
        self.__pk = None
        self.__ps = None
        self.__dk = user
        self.__ds = None
        self.__server = server
        self.__qos = qos
        self.__port = port
        self.__mqtt = None
        self.__clean_session = clean_session
        self.__life_time = life_time
        self.__client_id = client_id
        self.__password = pass_word

        if pub_topic == None:
            self.pub_topic_dict = {"0": "/python/mqtt/pub"}
        else:
            self.pub_topic_dict = pub_topic
        if sub_topic == None:
            self.sub_topic_dict = {"0": "/python/mqtt/sub"}
        else:
            self.sub_topic_dict = sub_topic

    def __subscribe_topic(self):
        for id, usr_sub_topic in self.sub_topic_dict.items():
            if self.__mqtt.subscribe(usr_sub_topic, qos=0) == -1:
                log.error("Topic [%s] Subscribe Falied." % usr_sub_topic)


    def __sub_cb(self, topic, data):
        """mqtt subscribe topic callback

        Parameter:
            topic: topic info
            data: response dictionary info
        """
        topic = topic.decode()

        try:
            self.notifyObservers(self, *("raw_data", {"topic":topic, "data":data} ) )
        except Exception as e:
            log.error("{}".format(e))

    def __listen(self):
        while True:
            self.__mqtt.wait_msg()
            utime.sleep_ms(100)

    def __start_listen(self):
        """Start a new thread to listen to the cloud publish 
        """
        _thread.start_new_thread(self.__listen, ())

    def init(self, enforce=False):
        """mqtt connect and subscribe topic

        Parameter:
            enforce:
                True: enfore cloud connect and subscribe topic
                False: check connect status, return True if cloud connected

        Return:
            Ture: Success
            False: Failed
        """
        log.debug("[init start] enforce: %s" % enforce)
        if enforce is False and self.__mqtt is not None:
            log.debug("self.get_status(): %s" % self.get_status())
            if self.get_status():
                return True

        if self.__mqtt is not None:
            self.close()
        
        log.debug("mqtt init. self.__client_id: %s, self.__password: %s, self.__dk: %s, self.__ds: %s" % (self.__client_id, self.__password, self.__dk, self.__ds))
        self.__mqtt = MQTTClient(client_id=self.__client_id, server=self.__server, port=self.__port,
                              user=self.__dk, password=self.__password, keepalive=self.__life_time, ssl=False)
        try:
            self.__mqtt.connect(clean_session=self.__clean_session)
        except Exception as e:
            log.error("mqtt connect error: %s" % e)
        else:
            self.__mqtt.set_callback(self.__sub_cb)
            self.__subscribe_topic()
            self.__start_listen()
            log.debug("mqtt start.")

        log.debug("self.get_status(): %s" % self.get_status())
        if self.get_status():
            return True
        else:
            return False

    def close(self):
        self.__mqtt.disconnect()

    def get_status(self):
        """Get mqtt connect status

        Return:
            True -- connect success
            False -- connect falied
        """
        try:
            return True if self.__mqtt.get_mqttsta() == 0 else False
        except:
            return False
    
    def through_post_data(self, data, topic_id):
        try:
            self.__mqtt.publish(self.pub_topic_dict[topic_id], data, self.__qos)
        except Exception:
            log.error("mqtt publish topic %s failed. data: %s" % (self.pub_topic_dict[topic_id], data))
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
