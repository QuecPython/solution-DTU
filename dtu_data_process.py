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
@file      :dtu_data_process.py
@author    :elian.wang@quectel.com
@brief     :Dtu parses and processes cloud and serial port data
@version   :0.1
@date      :2022-05-23 09:33:41
@copyright :Copyright (c) 2022
"""


import log
import utime
import ujson
from machine import Pin
from machine import UART
from usr.modules.common import Singleton
from usr.command_mode import CommandMode
from usr.modbus_mode import ModbusMode
from usr.through_mode import ThroughMode
from usr.modules.remote import RemotePublish
from usr.modules.logging import getLogger
from usr.dtu_channels import ChannelTransfer
from usr.settings import settings
from usr.dtu_crc import dtu_crc
from usr.settings import PROJECT_NAME, PROJECT_VERSION, DEVICE_FIRMWARE_NAME, DEVICE_FIRMWARE_VERSION

log = getLogger(__name__)

class DtuDataProcess(Singleton):
    """This is a class for process Dtu data.

    This class has the following functions:
        1.Uart init

        2. Parsing cloud data, Answer cloud data or send to uart

        3. Check OTA state
        3.1 Publish mcu and firmware ota plain request(topic:"/sys/pk/dk/thing/ota/firmware/get")
        3.2 Publish mcu and firmware name, version(topic:"/ota/device/inform/pk/dk")

        4.Read uart data

        5.Post history data to cloud

        6.Determine the parameters and perform the OTA plan

    Attribute:
        __serial_map(dict): key(str):uart id, value:uart object list
        __work_mode(object): ThroughMode() or CommandMode() or ModbusMode() instantiation
    """
    def __init__(self, settings):
        # 配置uart
        self.__serial_map = dict()
        for sid, conf in settings.get("uconf").items():
            uart_conn = UART(getattr(UART, "UART%d" % int(sid)),
                             int(conf.get("baudrate")),
                             int(conf.get("databits")),
                             int(conf.get("parity")),
                             int(conf.get("stopbits")),
                             int(conf.get("flowctl")))
            self.__serial_map[sid] = uart_conn
        # 初始化方向gpio
        self.__direction_pin(settings.get("direction_pin"))
        self.__work_mode_name = settings.get("work_mode")
        self.__work_mode = None
        self.__remote_pub = None
        self.__channel = None

    def add_module(self, module, callback=None):
        if isinstance(module, RemotePublish):
            self.__remote_pub = module
            return True
        elif isinstance(module, CommandMode) or isinstance(module, ModbusMode) or isinstance(module, ThroughMode):
            self.__work_mode = module
        elif isinstance(module, ChannelTransfer):
            self.__channel = module
            if isinstance(self.__work_mode, CommandMode):
                self.__work_mode.search_cmd.set_channel(module)

    def __remote_post_data(self, channel_id, topic_id=None, data=None):
        if not self.__remote_pub:
            raise TypeError("self.__remote_pub is not registered.")
        return self.__remote_pub.post_data(data, channel_id, topic_id)

    def __remote_ota_check(self, channel_id):
        if not self.__remote_pub:
            raise TypeError("self.__remote_pub is not registered.")
        return self.__remote_pub.cloud_ota_check(channel_id)

    def __remote_ota_action(self, channel_id, action, module):
        if not self.__remote_pub:
            raise TypeError("self.__remote_pub is not registered.")
        return self.__remote_pub.cloud_ota_action(channel_id, action, module)

    def __remote_device_report(self, channel_id):
        if not self.__remote_pub:
            raise TypeError("self.__remote_pub is not registered.")
        return self.__remote_pub.cloud_device_report(channel_id)

    def ota_check(self):
        print("ota_check")
        try:
            if settings.current_settings.get("ota"):
                for k, v in settings.current_settings.get("conf").items():
                    log.info("channel id{}".format(k))
                    self.__remote_ota_check(k)
                    self.__remote_device_report(k)
                    utime.sleep(1)
        except Exception as e:
            log.error("periodic_ota_check fault", e)

    def __direction_pin(self, direction_pin=None):
        """Config Rs485 Tx/Rx ctrl gpio and set gpio output level 

        Args:
            direction_pin (dict, optional): _description_. Defaults to None.
        """
        if direction_pin == None:
            return
        for sid, conf in direction_pin.items():
            uart = self.__serial_map.get(str(sid))
            gpio = getattr(Pin, "GPIO%s" % str(conf.get("GPIOn")))
            direction_level = conf.get("direction")
            uart.control_485(gpio, direction_level)

      
    def __gui_tools_parse(self, gui_data, sid):
        """Parse uart data in the format specified by the GUI

        Args:
            gui_data (bytes): data read from uart
            sid (str): uart channel id

        Returns:
            True: GUI data was successfully obtained
            False: get GUI data failed
        """
        print("Gui data parse")
        gui_data = gui_data.decode()
        data_list = gui_data.split(",", 3)
        if len(data_list) != 4:
            log.info("DTU CMD list length validate fail. CMD Parse end.")
            return False
        gui_code = data_list[0]
        if gui_code != "99":
            return False
        data_length = data_list[1]
        crc32_val = data_list[2]
        msg_data = data_list[3]
        try:
            data_len_int = int(data_length)
        except:
            log.error("DTU CMD data error.")
            return False
        if len(msg_data) > data_len_int:
            log.error("DTU CMD length validate failed.")
            return False
        elif len(msg_data) < data_len_int:
            log.info("Msg length shorter than length")
            return True
        data_crc = dtu_crc.crc32(msg_data)
        if crc32_val != data_crc:
            log.error("DTU CMD CRC32 vaildate failed")
            return False
        try:
            data = ujson.loads(msg_data)
        except Exception as e:
            log.error(e)
            return False
        cmd_code = data.get("cmd_code")
        # No command code was obtained
        if cmd_code is None:
            return False
        params_data = data.get("data")
        password = data.get("password", None)
        rec = self.__command_mode.exec_command_code(int(cmd_code), data=params_data, password=password)
        rec_str = ujson.dumps(rec)
        rec_crc_val = dtu_crc.crc32(rec_str)
        rec_format = "{},{},{}".format(len(rec_str), rec_crc_val, rec_str)
        # Gets the serialID of the data to be returned
        uart = self.__serial_map.get(str(sid))
        uart.write(rec_format.encode("utf-8"))
        print("GUI CMD SUCCESS")
        return True


    def cloud_read_data_parse_main(self, cloud, *args, **kwargs):
        """Parsing cloud data, Answer cloud data or send to serial port

        Args:
            cloud (cloud object): different cloud object,such as:AliYunIot、TXYunIot、QuecThing、HuaweiIot
            kwargs (dict): The data received by the cloud,contains topic and data
        """
        topic_id = None
        channel_id = None
        serial_id = None
        pkg_id = None
        request_id = None

        # 云端为MQTT/Aliyun/Txyun时可获取tpoic id
        if kwargs.get("topic") is not None:
            for k, v in cloud.sub_topic_dict.items():
                if kwargs["topic"] == v:
                    topic_id = k
        # 云端为quecthing 时，没有topic id 
        pkg_id = kwargs.get("pkgid", None)

        request_id = kwargs.get("request_id", None)

        if topic_id is not None:
            msg_id = topic_id   # aliyun\mqtt\huaweiyun\tenxunyun
        elif pkg_id is not None:
            msg_id = pkg_id     # quecthing
        elif request_id is not None:
            msg_id = request_id # http
        else:
            msg_id = None       #tcp\udp
        
        for k, v in self.__channel.cloud_object_dict.items():
            if cloud == v:
                channel_id = k
     
        for sid, cid in self.__channel.serial_channel_dict.items():
            if channel_id in cid:
                serial_id = sid

        if isinstance(kwargs["data"], bytes):
            data = kwargs["data"].decode()
        elif isinstance(kwargs["data"], dict):
            data = ujson.dumps(kwargs["data"])
        elif isinstance(kwargs["data"], str):
            data = kwargs["data"]
        else:
            data = str(kwargs["data"])
        ret_data = self.__work_mode.cloud_data_parse(data, msg_id, channel_id)

        # reply cloud query command
        if ret_data["cloud_data"] is not None:
            cloud_name = self.__channel.cloud_channel_dict[channel_id].get("protocol")
            if cloud_name in ["mqtt", "aliyun", "txyun", "hwyun"]:
                if "topic_id" in ret_data["cloud_data"]:
                    topic_id = ret_data["cloud_data"].pop("topic_id")
                    if not isinstance(topic_id, str):
                        topic_id = str(topic_id)
                else:
                    topic_id = list(cloud.pub_topic_dict.keys())[0] 
            else:
                topic_id = None
            str_data = ujson.dumps(ret_data["cloud_data"])

            self.__remote_post_data(channel_id, topic_id, data=str_data)
        #send to uart cloud message
        if ret_data["uart_data"] is not None:
            uart_port = self.__serial_map.get(str(serial_id))
            uart_port.write(ret_data["uart_data"])

    def uart_read_data_parse_main(self, data, sid):
        """Parsing uart data, send data to cloud

        Args:
            data (bytes): data read from uart
            sid (str): Uart id for data sources
        """
        
        cloud_channel_array = self.__channel.serial_channel_dict.get(int(sid))
        if not cloud_channel_array:
            log.error("Serial Config not exist!")
            return False
        # judgement is GUI command
        if self.__gui_tools_parse(data, sid) == True:
            return False
        
        send_params = self.__work_mode.uart_data_parse(data, self.__channel.cloud_channel_dict, cloud_channel_array)
        
        if len(send_params) == 3:
            self.__remote_post_data(channel_id=send_params[1], topic_id=send_params[2], data=send_params[0])
            return True
        elif len(send_params) == 2:
            self.__remote_post_data(channel_id=send_params[1], data=send_params[0])
            return True
        else:
            return False

    def read(self):
        """read data uart
        """
        while 1:
            for sid, uart in self.__serial_map.items():
                msgLen = uart.any()
                if msgLen:
                    msg = uart.read(msgLen)
                    try:
                        self.uart_read_data_parse_main(msg, sid)
                    except Exception as e:
                        log.error("UART handler error: %s" % e)
                        utime.sleep_ms(100)
                        continue
                else:
                    utime.sleep_ms(100)
                    continue

    def post_history_data(self, data):
        """Post history data to cloud

        Args:
            data (str): history data

        Returns:
            True: Successfully post
            False:Failure to post
        """
        log.info("post_history_data")
        # Obtain the channel_id of any channel in cloud channel configuration to send historical data
        channel_id = list(self.__channel.cloud_channel_dict.keys())[0]
        cloud_channel_config = self.__channel.cloud_channel_dict[channel_id]

        try:
            if cloud_channel_config.get("protocol") in ["tcp", "udp", "quecthing"]:
                return self.__remote_post_data(channel_id = channel_id, data=data)
            elif cloud_channel_config.get("protocol") is "http":
                request_ids = list(cloud_channel_config.get("request").keys())
                return self.__remote_post_data(channel_id = channel_id, topic_id=request_ids[0], data=data)
            else:
                print("protocol:", cloud_channel_config.get("protocol"))
                topics = list(cloud_channel_config.get("publish").keys())
                print("topics:", topics)
                return self.__remote_post_data(channel_id = channel_id, topic_id=topics[0], data=data)
        except Exception as e:
            log.error(e)
            return False

    def event_ota_plain(self, cloud, *args, **kwargs):
        """Determine the parameters and perform the OTA plan

        Args:
            cloud (cloud object): Call event_ota_plain
            args(tuple):Ota parameters sent from the cloud
            kwargs(dict):None
        """
        log.debug("ota_plain args: %s, kwargs: %s" % (str(args), str(kwargs)))
        current_settings = settings.get()

        for k, v in self.__channel.cloud_object_dict.items():
            if cloud == v:
                channel_id = k
        
        if cloud.cloud_name == "quecthing":
            if args and args[0]:
                if args[0][0] == "ota_cfg":
                    module = args[0][1].get("componentNo")
                    target_version = args[0][1].get("targetVersion")
                    if module == DEVICE_FIRMWARE_NAME and current_settings["ota"] == 1:
                        source_version = DEVICE_FIRMWARE_VERSION
                    elif module == PROJECT_NAME and current_settings["fota"] == 1:
                        source_version = PROJECT_VERSION
                    else:
                        return 
                    print("module:", module)
                    print("target_version:", target_version)
                    print("source_version:", source_version)
                    if target_version != source_version:
                        self.__remote_ota_action(channel_id, action=1, module=module)
        elif cloud.cloud_name == "aliyun":
            if args and args[0]:
                if args[0][0] == "ota_cfg":
                    module = args[0][1].get("module")
                    target_version = args[0][1].get("version")
                    if module == DEVICE_FIRMWARE_NAME and current_settings["ota"] == 1:
                        source_version = DEVICE_FIRMWARE_VERSION
                    elif module == PROJECT_NAME and current_settings["fota"] == 1:
                        source_version = PROJECT_VERSION
                    else:
                        return
                    if target_version != source_version:
                        self.__remote_ota_action(channel_id, action=1, module=module)
        else:
            log.error("Current Cloud (0x%X) Not Supported!" % current_settings["sys"]["cloud"])
