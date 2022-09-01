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
@file      :aliyunIot.py
@author    :Jack Sun (jack.sun@quectel.com)
@brief     :This file shows the interface of alicloud
@version   :0.1
@date      :2022-05-18 09:16:41
@copyright :Copyright (c) 2022
"""


import uos
import usys
import fota
import ujson
import utime
import uzlib
import ql_fs
import _thread
import osTimer
import uhashlib
import app_fota
import ubinascii
import app_fota_download

from misc import Power
from queue import Queue
from aLiYun import aLiYun
from usr.modules.logging import getLogger
from usr.modules.common import numiter, option_lock, CloudObservable, CloudObjectModel

log = getLogger(__name__)

_gps_read_lock = _thread.allocate_lock()

FOTA_ERROR_CODE = {
    1001: "FOTA_DOMAIN_NOT_EXIST",
    1002: "FOTA_DOMAIN_TIMEOUT",
    1003: "FOTA_DOMAIN_UNKNOWN",
    1004: "FOTA_SERVER_CONN_FAIL",
    1005: "FOTA_AUTH_FAILED",
    1006: "FOTA_FILE_NOT_EXIST",
    1007: "FOTA_FILE_SIZE_INVALID",
    1008: "FOTA_FILE_GET_ERR",
    1009: "FOTA_FILE_CHECK_ERR",
    1010: "FOTA_INTERNAL_ERR",
    1011: "FOTA_NOT_INPROGRESS",
    1012: "FOTA_NO_MEMORY",
    1013: "FOTA_FILE_SIZE_TOO_LARGE",
    1014: "FOTA_PARAM_SIZE_INVALID",
}


class AliObjectModel(CloudObjectModel):
    """This class is aliyun object model

    This class extend CloudObjectModel.

    Attribute:
        events:
            Attribute:
                - object model event
                - attribute value data format
                {
                    "sos_alert": {
                        local_time: 1651136994000
                    }
                }
        properties:
            Attribute:
                - object model property
                - attribute value data format
                {
                    "GeoLocation": {
                        "Longtitude": 0.0,
                        "Latitude": 0.0,
                        "Altitude": 0.0,
                        "CoordinateSystem": 0
                    }
                }
    """

    def __init__(self, om_file="/usr/aliyun_object_model.json"):
        super().__init__(om_file)
        self.init()

    def __init_value(self, om_type):
        if om_type in ("int", "enum", "date"):
            om_value = 0
        elif om_type in ("float", "double"):
            om_value = 0.0
        elif om_type == "bool":
            om_value = True
        elif om_type == "text":
            om_value = ""
        elif om_type == "array":
            om_value = []
        elif om_type == "struct":
            om_value = {}
        else:
            om_value = None
        return om_value

    def __get_property(self, om_item):
        om_item_key = om_item["identifier"]
        om_item_type = om_item["dataType"]["type"]
        om_item_val = self.__init_value(om_item_type)
        if om_item_type == "struct":
            om_item_struct = om_item["dataType"]["specs"]
            om_item_val = {i["identifier"]: self.__init_value(i["dataType"]["type"]) for i in om_item_struct}
        return om_item_key, om_item_val

    def __init_properties(self, om_properties):
        for om_property in om_properties:
            om_property_key, om_property_val = self.__get_property(om_property)
            setattr(self.properties, om_property_key, {om_property_key: om_property_val})

    def __init_events(self, om_events):
        for om_event in om_events:
            om_event_key = om_event["identifier"]
            om_event_out_put = om_event.get("outputData", [])
            om_event_val = {}
            if om_event_out_put:
                for om_property in om_event_out_put:
                    om_property_key, om_property_val = self.__get_property(om_property)
                    om_property_val[om_property_key] = om_property_val
            setattr(self.events, om_event_key, {om_event_key: om_event_val})

    def init(self):
        with open(self.om_file, "rb") as f:
            cloud_object_model = ujson.load(f)
            self.__init_properties(cloud_object_model.get("properties", []))
            self.__init_events(cloud_object_model.get("events", []))



class AliYunIot(CloudObservable):
    """This is a class for aliyun iot.

    This class extend CloudObservable.

    This class has the following functions:
        1. Cloud connect and disconnect

        2. Publish data to cloud
        2.1 Publish object module
        2.2 Publish ota device info, ota upgrade process, ota plain info request
        2.3 Publish rrpc response

        3. Subscribe data from cloud
        3.1 Subscribe publish object model result
        3.2 Subscribe cloud message
        3.3 Subscribe ota plain
        3.4 Subscribe rrpc request

    Attribute:
        ica_topic_property_post: topic for publish object model property
        ica_topic_property_post_reply: topic for subscribe publish object model property result
        ica_topic_property_set: topic for subscribe cloud object model property set
        ica_topic_event_post: topic for publish object model event
        ica_topic_event_post_reply: topic for subscribe publish object model event result
        ota_topic_device_inform: topic for publish device information
        ota_topic_device_upgrade: topic for subscribe ota plain
        ota_topic_device_progress: topic for publish ota upgrade process
        ota_topic_firmware_get: topic for publish ota plain request
        ota_topic_firmware_get_reply: topic for subscribe ota plain request response
        ota_topic_file_download: topic for publish ota mqtt file download request
        ota_topic_file_download_reply: topic for publish ota mqtt file download request response
        rrpc_topic_request: topic for subscribe rrpc message
        rrpc_topic_response: topic for publish rrpc response

    Run step:
        1. cloud = AliYunIot(pk, ps, dk, ds, server, client_id)
        2. cloud.addObserver(RemoteSubscribe)
        3. cloud.set_object_model(AliObjectModel)
        4. cloud.init()
        5. cloud.post_data(data)
        6. cloud.close()
    """

    def __init__(self, pk, ps, dk, ds, server, qos, client_id, pub_topic=None, sub_topic=None, burning_method=0, life_time=120,
                 mcu_name="", mcu_version="", firmware_name="", firmware_version="", reconn=True):
        """
        1. Init parent class CloudObservable
        2. Init cloud connect params and topic
        """
        super().__init__()
        self.__pk = pk
        self.__ps = ps
        self.__dk = dk
        self.__ds = ds
        self.__server = server
        self.__qos = qos
        self.__burning_method = burning_method
        self.__life_time = life_time
        self.__mcu_name = mcu_name
        self.__mcu_version = mcu_version
        self.__firmware_name = firmware_name
        self.__firmware_version = firmware_version
        self.__reconn = reconn
        self.__object_model = None
        self.__client_id = client_id

        self.__ali = None
        self.__post_res = {}
        self.__breack_flag = 0
        self.__ali_timer = osTimer()

        self.__id_iter = numiter()
        self.__id_lock = _thread.allocate_lock()

        self.__ota = AliOTA(self, self.__mcu_name, self.__firmware_name)
        if pub_topic == None:
            self.pub_topic_dict = {"0": "/%s/%s/user/update" % (self.__pk, self.__dk)}
        else:
            self.pub_topic_dict = pub_topic
        if sub_topic == None:
            self.sub_topic_dict = {"0": "/%s/%s/user/get" % (self.__pk, self.__dk)}
        else:
            self.sub_topic_dict = sub_topic

        self.ica_topic_property_post = "/sys/%s/%s/thing/event/property/post" % (self.__pk, self.__dk)
        self.ica_topic_property_post_reply = "/sys/%s/%s/thing/event/property/post_reply" % (self.__pk, self.__dk)
        self.ica_topic_property_set = "/sys/%s/%s/thing/service/property/set" % (self.__pk, self.__dk)
        self.ica_topic_event_post = "/sys/%s/%s/thing/event/{}/post" % (self.__pk, self.__dk)
        self.ica_topic_event_post_reply = "/sys/%s/%s/thing/event/{}/post_reply" % (self.__pk, self.__dk)
        self.ota_topic_device_inform = "/ota/device/inform/%s/%s" % (self.__pk, self.__dk)
        self.ota_topic_device_upgrade = "/ota/device/upgrade/%s/%s" % (self.__pk, self.__dk)
        self.ota_topic_device_progress = "/ota/device/progress/%s/%s" % (self.__pk, self.__dk)
        self.ota_topic_firmware_get = "/sys/%s/%s/thing/ota/firmware/get" % (self.__pk, self.__dk)
        self.ota_topic_firmware_get_reply = "/sys/%s/%s/thing/ota/firmware/get_reply" % (self.__pk, self.__dk)

        # TODO: To Download OTA File For MQTT Association (Not Support Now.)
        self.ota_topic_file_download = "/sys/%s/%s/thing/file/download" % (self.__pk, self.__dk)
        self.ota_topic_file_download_reply = "/sys/%s/%s/thing/file/download_reply" % (self.__pk, self.__dk)

        self.rrpc_topic_request = "/sys/%s/%s/rrpc/request/+" % (self.__pk, self.__dk)
        self.rrpc_topic_response = "/sys/%s/%s/rrpc/response/{}" % (self.__pk, self.__dk)

    def __get_id(self):
        """Get message id for publishing data"""
        with self.__id_lock:
            try:
                msg_id = next(self.__id_iter)
            except StopIteration:
                self.__id_iter = numiter()
                msg_id = next(self.__id_iter)

        return str(msg_id)

    def __put_post_res(self, msg_id, res):
        """Save publish result by message id

        Parameter:
            msg_id: publish message id
            res: publish result, True or False
        """
        self.__post_res[msg_id] = res

    def __ali_timer_cb(self, args):
        """osTimer callback to break cycling of get publish result"""
        self.__breack_flag = 1

    @option_lock(_gps_read_lock)
    def __get_post_res(self, msg_id):
        """Get publish result by message id

        Parameter:
            msg_id: publish message id

        Return:
            True: publish success
            False: publish failed
        """
        self.__ali_timer.start(1000 * 10, 0, self.__ali_timer_cb)
        while self.__post_res.get(msg_id) is None:
            if self.__breack_flag:
                self.__post_res[msg_id] = False
                break
            utime.sleep_ms(50)
        self.__ali_timer.stop()
        self.__breack_flag = 0
        res = self.__post_res.pop(msg_id)
        return res

    def __subscribe_topic(self, topic, qos=0):
        subscribe_res = self.__ali.subscribe(topic, qos=0)
        if subscribe_res == -1:
            raise TypeError("AliYun subscribe topic %s falied" % topic)

    def __ali_subscribe_topic(self):
        """Subscribe aliyun topic"""
        try:
            """
            self.__subscribe_topic(self.ica_topic_property_post)
            self.__subscribe_topic(self.ica_topic_property_post_reply)
            self.__subscribe_topic(self.ica_topic_property_set)
            """
            self.__subscribe_topic(self.ota_topic_device_upgrade, self.__qos)
            self.__subscribe_topic(self.ota_topic_firmware_get_reply, self.__qos)
            """
            self.__subscribe_topic(self.rrpc_topic_request)

            for tsl_event_identifier in self.__object_model.events.__dict__.keys():
                post_topic = self.ica_topic_event_post.format(tsl_event_identifier)
                self.__subscribe_topic(post_topic)
                post_reply_topic = self.ica_topic_event_post_reply.format(tsl_event_identifier)
                self.__subscribe_topic(post_reply_topic)

            # TODO: To Download OTA File For MQTT Association (Not Support Now.)
            self.__subscribe_topic(self.ota_topic_file_download_reply)
            """
            for id, usr_sub_topic in self.sub_topic_dict.items():
                self.__subscribe_topic(usr_sub_topic, self.__qos)

            return True
        except Exception as e:
            usys.print_exception(e)
            log.error(e)
            return False

    def __ali_sub_cb(self, topic, data):
        """Aliyun subscribe topic callback

        Parameter:
            topic: topic info
            data: response dictionary info
        """
        topic = topic.decode()
        try:
            data = ujson.loads(data)
        except:
            pass
        log.info("topic: %s, data: %s" % (topic, data))
        if topic.endswith("/post_reply"):
            self.__put_post_res(data["id"], True if data["code"] == 200 else False)
        elif topic.endswith("/property/set"):
            if data["method"] == "thing.service.property.set":
                dl_data = list(zip(data.get("params", {}).keys(), data.get("params", {}).values()))
                self.notifyObservers(self, *("object_model", dl_data))
        elif topic.startswith("/ota/device/upgrade/"):
            self.__put_post_res(data["id"], True if int(data["code"]) == 1000 else False)
            if int(data["code"]) == 1000:
                if data.get("data"):
                    self.__ota.set_ota_info(data["data"])
                    self.notifyObservers(self, *("object_model", [("ota_status", (data["data"]["module"], 1, data["data"]["version"]))]))
                    self.notifyObservers(self, *("ota_plain", [("ota_cfg", data["data"])]))
        elif topic.endswith("/thing/ota/firmware/get_reply"):
            self.__put_post_res(data["id"], True if int(data["code"]) == 200 else False)
            if data["code"] == 200:
                if data.get("data"):
                    self.__ota.set_ota_info(data["data"])
                    self.notifyObservers(self, *("object_model", [("ota_status", (data["data"]["module"], 1, data["data"]["version"]))]))
                    self.notifyObservers(self, *("ota_plain", [("ota_cfg", data["data"])]))
        # TODO: To Download OTA File For MQTT Association (Not Support Now.)
        elif topic.endswith("/thing/file/download_reply"):
            self.__put_post_res(data["id"], True if int(data["code"]) == 200 else False)
            if data["code"] == 200:
                self.notifyObservers(self, *("ota_file_download", data["data"]))
        elif topic.find("/rrpc/request/") != -1:
            message_id = topic.split("/")[-1]
            self.notifyObservers(self, *("rrpc_request", {"message_id": message_id, "data": data}))
        else:
            try:
                self.notifyObservers(self, *("raw_data", {"topic":topic, "data":data} ) )
            except Exception as e:
                log.error("{}".format(e))
    

    def __data_format(self, data):
        """Publish data format by AliObjectModel

        Parameter:
            data format:
            {
                "phone_num": "123456789",
                "energy": 100,
                "GeoLocation": {
                    "Longtitude": 100.26,
                    "Latitude": 26.86,
                    "Altitude": 0.0,
                    "CoordinateSystem": 1
                },
            }

        Return:
            {
                "event": [
                    {
                        "id": 1,
                        "version": "1.0",
                        "sys": {
                            "ack": 1
                        },
                        "params": {
                            "sos_alert": {
                                "value": {},
                                "time": 1649991780000
                            },
                        },
                        "method": "thing.event.sos_alert.post"
                    }
                ],
                "property": [
                    {
                        "id": 2,
                        "version": "1.0",
                        "sys": {
                            "ack": 1
                        },
                        "params": {
                            "phone_num": {
                                "value": "123456789",
                                "time": 1649991780000
                            },
                            "energy": {
                                "value": 100,
                                "time": 1649991780000
                            },
                        },
                        "method": "thing.event.property.post"
                    }
                ],
                "msg_ids": [1, 2],
                "event_topic": {
                    1: "/sys/{product_key}/{device_key}/thing/event/{event}/post",
                    2: "/sys/{product_key}/{device_key}/thing/event/property/post",
                }
            }
        """
        res = {"property": [], "event": [], "event_topic": {}, "service": [], "service_topic": {}, "msg_ids": []}
        property_params = {}
        event_params = {}
        service_params = {}
        # Format Publish Params.
        for k, v in data.items():
            if hasattr(self.__object_model.properties, k):
                property_params[k] = {
                    "value": v,
                    "time": utime.mktime(utime.localtime()) * 1000
                }
            elif hasattr(self.__object_model.events, k):
                event_params[k] = {
                    "value": {},
                    "time": utime.mktime(utime.localtime()) * 1000
                }
            elif hasattr(self.__object_model.services, k):
                service_params[k] = v
            else:
                log.error("Publish Key [%s] is not in property and event" % k)

        if property_params:
            msg_id = self.__get_id()
            publish_data = {
                "id": msg_id,
                "version": "1.0",
                "sys": {
                    "ack": 1
                },
                "params": property_params,
                "method": "thing.event.property.post"
            }
            res["property"].append(publish_data)
            res["msg_ids"].append(msg_id)

        if event_params:
            for event in event_params.keys():
                topic = self.ica_topic_event_post.format(event)
                msg_id = self.__get_id()
                publish_data = {
                    "id": msg_id,
                    "version": "1.0",
                    "sys": {
                        "ack": 1
                    },
                    "params": event_params[event],
                    "method": "thing.event.%s.post" % event
                }
                res["event"].append(publish_data)
                res["event_topic"][msg_id] = topic
                res["msg_ids"].append(msg_id)

        if service_params:
            """Service params value:
            {
                "id": "123",
                "code": 200,
                "message": "success",
                "data": {
                    "output_data_key": "output_data_val",
                    ...
                }
            }
            """
            for service in service_params.keys():
                topic = self.ica_topic_service_pub_reply.format(service)
                if service_params[service].get("id") is None:
                    log.error("Service %s id is not exists. params: %s" % (service, str(service_params[service])))
                    continue
                msg_id = service_params[service]["id"]
                publish_data = service_params[service]
                publish_data.update({"version": "1.0"})
                res["service"].append(publish_data)
                res["service_topic"][msg_id] = topic
                res["msg_ids"].append(msg_id)

        return res

    def set_object_model(self, object_model):
        """Register AliObjectModel to this class"""
        if object_model and isinstance(object_model, AliObjectModel):
            self.__object_model = object_model
            return True
        return False

    def init(self, enforce=False):
        """Aliyun connect and subscribe topic

        Parameter:
            enforce:
                True: enfore cloud connect and subscribe topic
                False: check connect status, return True if cloud connected

        Return:
            Ture: Success
            False: Failed
        """
        log.debug("[init start] enforce: %s" % enforce)
        if enforce is False and self.__ali is not None:
            log.debug("self.get_status(): %s" % self.get_status())
            if self.get_status():
                return True

        if self.__ali is not None:
            self.close()

        if self.__burning_method == 0:
            self.__dk = None
        elif self.__burning_method == 1:
            self.__ps = None

        log.debug("aLiYun init. self.__pk: %s, self.__ps: %s, self.__dk: %s, self.__ds: %s, self.__server: %s" % (self.__pk, self.__ps, self.__dk, self.__ds, self.__server))
        self.__ali = aLiYun(self.__pk, self.__ps, self.__dk, self.__ds, self.__server)
        log.debug("aLiYun setMqtt.")
        setMqttres = self.__ali.setMqtt(self.__client_id, clean_session=False, keepAlive=self.__life_time, reconn=True)
        log.debug("aLiYun setMqttres: %s" % setMqttres)
        if setMqttres != -1:
            setCallbackres = self.__ali.setCallback(self.__ali_sub_cb)
            log.debug("aLiYun setCallback: %s" % setCallbackres)
            subs_res = self.__ali_subscribe_topic()
            log.debug("aLiYun __ali_subscribe_topic subs_res: %s" % subs_res)
            if subs_res is True:
                self.__ali.start()
                log.debug("aLiYun start.")
            else:
                log.error("aLiYun subscribe falied and to disconnect.")
                self.close()
                self.__ali = None
                return False
        else:
            log.error("setMqtt falied!")
            self.close()
            self.__ali = None
            return False

        log.debug("self.get_status(): %s" % self.get_status())
        if self.get_status():
            return True
        else:
            return False

    def close(self):
        """Aliyun disconnect"""
        try:
            self.__ali.disconnect()
        except Exception as e:
            log.error("Ali disconnect falied. %s" % e)
        return True

    def get_status(self):
        """Get aliyun connect status

        Return:
            True -- connect success
           False -- connect falied
        """
        try:
            return True if self.__ali.getAliyunSta() == 0 else False
        except:
            return False

    def post_data(self, data):
        """Publish object model property, event

        Parameter:
            data format:
            {
                "phone_num": "123456789",
                "energy": 100,
                "GeoLocation": {
                    "Longtitude": 100.26,
                    "Latitude": 26.86,
                    "Altitude": 0.0,
                    "CoordinateSystem": 1
                },
            }

        Return:
            Ture: Success
            False: Failed
        """
        try:
            publish_data = self.__data_format(data)
            # Publish Property Data.
            for item in publish_data["property"]:
                self.__ali.publish(self.ica_topic_property_post, ujson.dumps(item), qos=0)
            # Publish Event Data.
            for item in publish_data["event"]:
                self.__ali.publish(publish_data["event_topic"][item["id"]], ujson.dumps(item), qos=0)
            # Publish Service Data.
            for item in publish_data["service"]:
                res = self.__ali.publish(publish_data["service_topic"][item["id"]], ujson.dumps(item), qos=0)
                log.debug("message_id: %s, res: %s" % (item["id"], res))
                self.__put_post_res(item["id"], res)

            pub_res = [self.__get_post_res(msg_id) for msg_id in publish_data["msg_ids"]]
            return True if False not in pub_res else False
        except Exception:
            log.error("AliYun publish failed. data: %s" % str(data))

        return False

    def through_post_data(self, data, topic_id):
        try:
            res = self.__ali.publish(self.pub_topic_dict[topic_id], data, qos=self.__qos)
            print("res:", res)
            return res
        except Exception:
            log.error("AliYun publish topic %s failed. data: %s" % (self.pub_topic_dict[topic_id], data))
            return False

    def rrpc_response(self, message_id, data):
        """Publish rrpc response

        Parameter:
            message_id: rrpc request messasge id
            data: response message

        Return:
            Ture: Success
            False: Failed
        """
        log.debug("rrpc_response message_id: %s" % message_id)
        topic = self.rrpc_topic_response.format(message_id)
        log.debug("rrpc_response topic: %s" % topic)
        pub_data = ujson.dumps(data) if isinstance(data, dict) else data
        log.debug("rrpc_response pub_data: %s" % pub_data)
        res = self.__ali.publish(topic, pub_data, qos=0)
        log.debug("rrpc_response res: %s" % res)
        return res

    def device_report(self):
        """Publish mcu and firmware name, version

        Return:
            Ture: Success
            False: Failed
        """
        muc_res = self.ota_device_inform(self.__mcu_version, module=self.__mcu_name)
        fw_res = self.ota_device_inform(self.__firmware_version, module=self.__firmware_name)
        return True if muc_res and fw_res else False

    def ota_request(self):
        """Publish mcu and firmware ota plain request

        Return:
            Ture: Success
            False: Failed
        """
        sota_res = self.ota_firmware_get(self.__mcu_name)
        fota_res = self.ota_firmware_get(self.__firmware_name)
        return True if sota_res and fota_res else False

    def ota_action(self, action, module=None):
        """Publish ota upgrade start or cancel ota upgrade

        Parameter:
            action: confirm or cancel upgrade
                - 0: cancel upgrade
                - 1: confirm upgrade

            module: mcu or firmare model name
                - e.g.: `QuecPython-Tracker`, `EC600N-CNLC`

        Return:
            Ture: Success
            False: Failed
        """
        if not module:
            log.error("Params[module] Is Empty.")
            return False
        if action not in (0, 1):
            log.error("Params[action] Should Be 0 Or 1, Not %s." % action)
            return False

        if action == 1:
            # if self.ota_device_progress(step=1, module=module):
            return self.__ota.start_ota()
        else:
            self.__ota.set_ota_info("", "", [])
            return self.ota_device_progress(step=-1, desc="User cancels upgrade.", module=module)

        return False

    def ota_device_inform(self, version, module="default"):
        """Publish device information

        Parameter:
            version: module version
                - e.g.: `2.1.0`

            module: mcu or firmare model name
                - e.g.: `QuecPython-Tracker`

        Return:
            Ture: Success
            False: Failed
        """
        msg_id = self.__get_id()
        publish_data = {
            "id": msg_id,
            "params": {
                "version": version,
                "module": module
            }
        }
        publish_res = self.__ali.publish(self.ota_topic_device_inform, ujson.dumps(publish_data), qos=0)
        log.debug("version: %s, module: %s, publish_res: %s" % (version, module, publish_res))
        return publish_res

    def ota_device_progress(self, step, desc, module="default"):
        """Publish ota upgrade process

        Parameter:
            step: upgrade process
                - 1 ~ 100: Upgrade progress percentage
                - -1: Upgrade failed
                - -2: Download failed
                - -3: Verification failed
                - -4: Programming failed

            desc: Description of the current step, no more than 128 characters long. If an exception occurs, this field can carry error information.

            module: mcu or firmare model name
                - e.g.: `QuecPython-Tracker`

        Return:
            Ture: Success
            False: Failed
        """
        msg_id = self.__get_id()
        publish_data = {
            "id": msg_id,
            "params": {
                "step": step,
                "desc": desc,
                "module": module,
            }
        }
        publish_res = self.__ali.publish(self.ota_topic_device_progress, ujson.dumps(publish_data), qos=0)
        if publish_res:
            return self.__get_post_res(msg_id)
        else:
            log.error("ota_device_progress publish_res: %s" % publish_res)
            return False

    def ota_firmware_get(self, module):
        """Publish ota plain info request

        Parameter:
            module: mcu or firmare model name
                - e.g.: `QuecPython-Tracker`

        Return:
            Ture: Success
            False: Failed
        """
        msg_id = self.__get_id()
        publish_data = {
            "id": msg_id,
            "version": "1.0",
            "params": {
                "module": module,
            },
            "method": "thing.ota.firmware.get"
        }
        publish_res = self.__ali.publish(self.ota_topic_firmware_get, ujson.dumps(publish_data), qos=0)
        log.debug("module: %s, publish_res: %s" % (module, publish_res))
        if publish_res:
            return self.__get_post_res(msg_id)
        else:
            log.error("ota_firmware_get publish_res: %s" % publish_res)
            return False

    def ota_file_download(self, fileToken, streamId, fileId, size, offset):
        """Publish mqtt ota plain file info request

        Parameter:
            fileToken: The unique identification Token of the file
            streamId: The unique identifier when downloading the OTA upgrade package through the MQTT protocol.
            fileId: Unique identifier for a single upgrade package file.
            size: The size of the file segment requested to be downloaded, in bytes. The value range is 256 B~131072 B. If it is the last file segment, the value ranges from 1 B to 131072 B.
            offset: The starting address of the bytes corresponding to the file fragment. The value range is 0~16777216.

        Return:
            Ture: Success
            False: Failed
        """
        msg_id = self.__get_id()
        publish_data = {
            "id": msg_id,
            "version": "1.0",
            "params": {
                "fileToken": fileToken,
                "fileInfo": {
                    "streamId": streamId,
                    "fileId": fileId
                },
                "fileBlock": {
                    "size": size,
                    "offset": offset
                }
            }
        }
        publish_res = self.__ali.publish(self.ota_topic_file_download, ujson.dumps(publish_data), qos=0)
        if publish_res:
            return self.__get_post_res(msg_id)
        else:
            log.error("ota_file_download publish_res: %s" % publish_res)
            return False


class AliOTA(object):

    def __init__(self, aliyuniot, mcu_name, firmware_name):
        self.__files = []
        self.__module = ""
        self.__version = ""
        self.__aliyuniot = aliyuniot
        self.__mcu_name = mcu_name
        self.__firmware_name = firmware_name
        self.__fota_queue = Queue(maxsize=4)

        self.__file_hash = None
        self.__tar_file = "sotaFile.tar.gz"
        self.__updater_dir = "/usr/.updater/"
        self.__ota_timer = osTimer()

    def __fota_callback(self, args):
        down_status = args[0]
        down_process = args[1]
        if down_status in (0, 1):
            log.debug("DownStatus: %s [%s][%s%%]" % (down_status, "=" * down_process, down_process))
            if down_process < 100:
                self.__aliyuniot.ota_device_progress(down_process, "Downloading File.", module=self.__module)
            else:
                self.__aliyuniot.ota_device_progress(100, "Download File Over.", module=self.__module)
                self.__set_upgrade_status(3)
                self.__fota_queue.put(True)
        elif down_status == 2:
            self.__aliyuniot.ota_device_progress(100, "Download File Over.", module=self.__module)
            self.__set_upgrade_status(3)
            self.__fota_queue.put(True)
        else:
            log.error("Down Failed. Error Code [%s] %s" % (down_process, FOTA_ERROR_CODE.get(down_process, down_process)))
            self.__aliyuniot.ota_device_progress(-2, FOTA_ERROR_CODE.get(down_process, down_process), module=self.__module)
            self.__fota_queue.put(False)

    def __ota_timer_callback(self, args):
        self.__aliyuniot.ota_device_progress(-1, "Download File Falied.", module=self.__module)
        self.__fota_queue.put(False)

    def __get_file_size(self, data):
        size = data.decode("ascii")
        size = size.rstrip("\0")
        if (len(size) == 0):
            return 0
        size = int(size, 8)
        return size

    def __get_file_name(self, name):
        file_name = name.decode("ascii")
        file_name = file_name.rstrip("\0")
        return file_name

    def __check_md5(self, cloud_md5):
        log.debug("AliOTA __check_md5")
        file_md5 = ubinascii.hexlify(self.__file_hash.digest()).decode("ascii")
        msg = "DMP Calc MD5 Value: %s, Device Calc MD5 Value: %s" % (cloud_md5, file_md5)
        log.debug(msg)
        if (cloud_md5 != file_md5):
            self.__aliyuniot.ota_device_progress(-3, "MD5 Verification Failed. %s" % msg, module=self.__module)
            log.error("MD5 Verification Failed")
            return False

        log.debug("MD5 Verification Success.")
        return True

    def __start_fota(self):
        log.debug("AliOTA __start_fota")
        fota_obj = fota()
        url1 = self.__files[0]["url"]
        url2 = self.__files[1]["url"] if len(self.__files) > 1 else ""
        log.debug("AliOTA start httpDownload")
        if url2:
            res = fota_obj.httpDownload(url1=url1, url2=url2, callback=self.__fota_callback)
        else:
            res = fota_obj.httpDownload(url1=url1, callback=self.__fota_callback)
        log.debug("AliOTA httpDownload res: %s" % res)
        if res == 0:
            self.__ota_timer.start(1000 * 3600, 0, self.__ota_timer_callback)
            fota_res = self.__fota_queue.get()
            self.__ota_timer.stop()
            return fota_res
        else:
            self.__set_upgrade_status(4)
            self.__aliyuniot.ota_device_progress(-2, "Download File Failed.", module=self.__module)
            return False

    def __start_sota_tar(self):
        log.debug("AliOTA __start_sota_tar")
        count = 0
        for index, file in enumerate(self.__files):
            if self.__download(file["url"]):
                if self.__check_md5(file["md5"]):
                    if self.__upgrade(self.__unzip()):
                        count += 1
            if index + 1 != count:
                break
        if count == len(self.__files):
            self.__set_upgrade_status(3)
        else:
            self.__set_upgrade_status(4)

        app_fota_download.set_update_flag()
        Power.powerRestart()

    def __start_sota(self):
        log.debug("AliOTA __start_sota")
        app_fota_obj = app_fota.new()
        download_infos = [{"url": i["url"], "file_name": i["file_name"]} for i in self.__files]
        bulk_download_res = app_fota_obj.bulk_download(download_infos)
        log.debug("first bulk_download_res: %s" % str(bulk_download_res))
        count = 0
        while bulk_download_res:
            bulk_download_res = app_fota_obj.bulk_download(bulk_download_res)
            log.debug("[%s]retry bulk_download_res: %s" % (count, str(bulk_download_res)))
            if bulk_download_res:
                count += 1
            if count > 3 and bulk_download_res:
                break
        if not bulk_download_res:
            self.__aliyuniot.ota_device_progress(100, "Download File Over.", module=self.__module)
            self.__set_upgrade_status(3)
            app_fota_obj.set_update_flag()
            Power.powerRestart()
        else:
            self.__set_upgrade_status(4)
            self.__aliyuniot.ota_device_progress(-2, "Download File Failed.", module=self.__module)

    def __download(self, url):
        log.debug("AliOTA __download")
        res = app_fota_download.download(url, self.__tar_file)
        if res == 0:
            self.__file_hash = uhashlib.md5()
            with open(self.__updater_dir + self.__tar_file, "rb+") as fp:
                for fpi in fp.readlines():
                    self.__file_hash.update(fpi)
            return True
        else:
            self.__aliyuniot.ota_device_progress(-2, "Download File Failed.", module=self.__module)
            return False

    def __unzip_size(self, tar_size):
        # TDOO: To Sure unzip size is file size or tar size
        file_size = tar_size * 2
        for i in range(1, 19):
            if file_size <= 1 << i:
                break
        log.debug("__unzip_size file_size: %s, zlibsize: %s" % (file_size, i))
        return i * -1

    def __unzip(self):
        log.debug("AliOTA __unzip")
        file_list = []
        tar_size = uos.stat(self.__updater_dir + self.__tar_file)[-4]
        with open(self.__updater_dir + self.__tar_file, "rb+") as ota_file:
            ota_file.seek(10)
            unzipFp = uzlib.DecompIO(ota_file, self.__unzip_size(tar_size))
            log.debug("[OTA Upgrade] Unzip file success.")
            # try:
            if True:
                while True:
                    data = unzipFp.read(0x200)
                    if not data:
                        log.debug("[OTA Upgrade] Read file size zore.")
                        break

                    size = self.__get_file_size(data[124:135])
                    file_name = self.__get_file_name(data[:100])
                    log.debug("[OTA Upgrade] File Name: %s, File Size: %s" % (file_name, size))

                    if not size:
                        if len(file_name):
                            log.debug("[OTA Upgrade] Create file: %s" % self.__updater_dir + file_name)
                            ql_fs.mkdirs(self.__updater_dir + file_name)
                        else:
                            log.debug("[OTA Upgrade] Have no file unzip.")
                            break
                    else:
                        log.debug("File %s write size %s" % (self.__updater_dir + file_name, size))
                        with open(self.__updater_dir + file_name, "wb+") as fp:
                            read_size = 0x200
                            last_size = size
                            while last_size > 0:
                                log.debug("read_size: %s, last_size: %s" % (read_size, last_size))
                                read_size = read_size if read_size <= last_size else last_size
                                data = unzipFp.read(read_size)
                                fp.write(data)
                                last_size -= read_size
                            log.debug("file_name: %s, size: %s" % (file_name, size))
                            file_list.append({"file_name": file_name, "size": size})
                log.debug("Remove %s" % (self.__updater_dir + self.__tar_file))
                uos.remove(self.__updater_dir + self.__tar_file)
                app_fota_download.delete_update_file(self.__tar_file)
            # except Exception as e:
            #     err_msg = "Unpack Error: %s" % e
            #     log.error(err_msg)
            #     self.__aliyuniot.ota_device_progress(-4, err_msg, module=self.__module)

        return file_list

    def __upgrade(self, file_list):
        log.debug("AliOTA __upgrade")

        if file_list:
            for file_name in file_list:
                app_fota_download.update_download_stat(self.__updater_dir + file_name["file_name"], "/usr/" + file_name["file_name"], file_name["size"])

            return True
        return False

    def __set_upgrade_status(self, upgrade_status):
        log.debug("__set_upgrade_status upgrade_status %s" % upgrade_status)
        #self.__aliyuniot.notifyObservers(self, *("object_model", [("ota_status", (self.__module, upgrade_status, self.__version))]))

    def set_ota_info(self, data):
        """
        upgrade_file:
        {
            "files": {
                "upgrade_file_name": "target_full_path_file_name"
            }
        }
        """
        upgrade_file = {}
        self.__module = data["module"]
        self.__version = data["version"]
        if self.__module == self.__mcu_name:
            upgrade_file = data.get("extData", {}).get("_package_udi")
            if upgrade_file:
                upgrade_file = ujson.loads(upgrade_file).get("files", {})
            else:
                log.error("Upgrade file comment is not exists.")
                return
        if data.get("files"):
            files = [{"size": i["fileSize"], "url": i["fileUrl"], "md5": i["fileMd5"], "file_name": upgrade_file.get(i["fileName"], "")} for i in data["files"]]
        else:
            name = ""
            for k, v in upgrade_file.items():
                name = v
                break
            files = [{"size": data["size"], "url": data["url"], "md5": data["md5"], "file_name": name}]
        self.__files = files

    def start_ota(self):
        log.debug("AliOTA start_ota module %s" % self.__module)
        self.__set_upgrade_status(2)
        if self.__module == self.__firmware_name:
            # self.__start_fota()
            _thread.start_new_thread(self.__start_fota, ())
        elif self.__module == self.__mcu_name:
            # self.__start_sota()
            _thread.start_new_thread(self.__start_sota, ())

        return True

