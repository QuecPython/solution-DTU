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
@file      :dtu_transaction.py
@author    :elian.wang@quectel.com
@brief     :Dtu transaction related interfaces
@version   :0.1
@date      :2022-08-04 11:33:23
@copyright :Copyright (c) 2022
"""


import log
import sim
import net
import usys
import ujson
import utime
import modem
import _thread
from misc import Power
from usr.modules.common import Singleton
from usr.modules.logging import getLogger
from usr.modules.serial import Serial
from usr.modules.remote import RemotePublish
from usr.modules.history import History
from usr.settings import settings
from usr.settings import PROJECT_NAME, PROJECT_VERSION, DEVICE_FIRMWARE_NAME, DEVICE_FIRMWARE_VERSION

log = getLogger(__name__)

class DownlinkTransaction(Singleton):
    """Data downlink:Receive data from the cloud and send it to serial
    """
    def __init__(self):
        self.__serial = None

    def add_module(self, module, callback=None):
        if isinstance(module, Serial):
            self.__serial = module
            return True
        return False

    def __get_sub_topic_id(self, topic):
        """Locate the topic id from the cloud setting

        Args:
            topic (str): topic in mqtt protocol 

        Returns:
            str: topic id
        """
        cloud_name = settings.current_settings["system_config"]["cloud"]
        cloud_config = settings.current_settings.get(cloud_name + "_config")
        if cloud_config == None:
            raise Exception("Cloud config parameter error")
        for k, v in cloud_config.get("subscribe").items():
            if topic == v:
                return k

    def downlink_main(self, *args, **kwargs):
        """Parsing cloud data, send to serial port

        Args:
            args (tuple): Not use
            kwargs (dict): The data received by the cloud,contains topic and data
        """
        # Get mqtt protocol message id
        cloud_type = settings.current_settings["system_config"]["cloud"]
        if cloud_type in ["aliyun", "txyun", "hwyun", "mqtt_private_cloud"]:
            msg_id = self.__get_sub_topic_id(kwargs.get("topic"))
            if msg_id == None:
                raise Exception("Not found correct topic id")
        elif cloud_type == "quecthing":
            msg_id = kwargs.get("pkgid")
        elif cloud_type == "tcp_private_cloud":
            msg_id = None
        else:
            raise Exception("This cloud is not support now")

        if isinstance(kwargs["data"], bytes):
            data = kwargs["data"].decode()
        elif isinstance(kwargs["data"], dict):
            data = ujson.dumps(kwargs["data"])
        elif isinstance(kwargs["data"], str):
            data = kwargs["data"]
        else:
            data = str(kwargs["data"])

        if cloud_type == "tcp_private_cloud":
            packed_data = data
        else:
            packed_data = "%s,%s,%s".encode('utf-8') % (str(msg_id), str(len(data)), data)
        # Send packed data through serial
        self.__serial.write(packed_data)    


class OtaTransaction(Singleton):
    """Device firmware OTA and project file OTA transaction
    """
    def __init__(self):
        self.__remote_pub = None

    def __remote_ota_check(self):
        if not self.__remote_pub:
            raise TypeError("self.__remote_pub is not registered.")
        return self.__remote_pub.cloud_ota_check()

    def __remote_ota_action(self, action, module):
        if not self.__remote_pub:
            raise TypeError("self.__remote_pub is not registered.")
        return self.__remote_pub.cloud_ota_action(action, module)

    def __remote_device_report(self):
        if not self.__remote_pub:
            raise TypeError("self.__remote_pub is not registered.")
        return self.__remote_pub.cloud_device_report()

    def add_module(self, module, callback=None):
        if isinstance(module, RemotePublish):
            self.__remote_pub = module
            return True
        return False

    def ota_check(self):
        """After powering on, release module information and check for update
        """
        print("ota_check")
        try:
            if settings.current_settings["system_config"]["base_function"]["fota"]:
                self.__remote_ota_check()
                self.__remote_device_report()
                utime.sleep(1)
        except Exception as e:
            log.error("periodic_ota_check fault", e)

    def event_ota_plain(self, *args, **kwargs):
        """Determine the parameters and perform the OTA plan

        Args:
            args (tuple): Ota parameters sent from the cloud
            kwargs (dict): None
        """
        log.debug("ota_plain args: %s, kwargs: %s" % (str(args), str(kwargs)))
        current_settings = settings.get()
        
        if current_settings["system_config"]["cloud"] == "quecthing":
            if args and args[0]:
                if args[0][0] == "ota_cfg":
                    module = args[0][1].get("componentNo")
                    target_version = args[0][1].get("targetVersion")
                    if module == DEVICE_FIRMWARE_NAME and current_settings["system_config"]["base_function"]["fota"] == True:
                        source_version = DEVICE_FIRMWARE_VERSION
                    elif module == PROJECT_NAME and current_settings["system_config"]["base_function"]["sota"] == True:
                        source_version = PROJECT_VERSION
                    else:
                        return
                    if target_version != source_version:
                        self.__remote_ota_action(action=1, module=module)
        elif current_settings["system_config"]["cloud"] == "aliyun":
            if args and args[0]:
                if args[0][0] == "ota_cfg":
                    module = args[0][1].get("module")
                    target_version = args[0][1].get("version")
                    if module == DEVICE_FIRMWARE_NAME and current_settings["system_config"]["base_function"]["fota"] == 1:
                        source_version = DEVICE_FIRMWARE_VERSION
                    elif module == PROJECT_NAME and current_settings["system_config"]["base_function"]["sota"] == 1:
                        source_version = PROJECT_VERSION
                    else:
                        return
                    if target_version != source_version:
                        self.__remote_ota_action(action=1, module=module)
        else:
            log.error("Current Cloud Not Supported OTA!")

class UplinkTransaction(Singleton):
    """Data uplink: read data from the serial and send it to cloud
    """
    def __init__(self):
        self.__remote_pub = None
        self.__serial = None
        self.__history = None
        self.__gui_tools_interac = None
        self.__parse_data = ""
        self.__send_to_cloud_data = []

    def __remote_post_data(self, data=None, topic_id=None):
        if not self.__remote_pub:
            raise TypeError("self.__remote_pub is not registered.")
        return self.__remote_pub.post_data(data, topic_id)

    def __get_pub_topic_id_list(self):
        """Get the publish topic id list in setting

        Returns:
            str: publist topic id list
        """
        cloud_name = settings.current_settings["system_config"]["cloud"]
        cloud_config = settings.current_settings.get(cloud_name + "_config")
        if cloud_config == None:
            raise Exception("Cloud config parameter error")
        elif cloud_name == "quecthing":
            return ["0"]
        else:
            return cloud_config.get("subscribe").keys()

    def __parse(self):
        """Recursive parse uart data
        """
        params_list = self.__parse_data.split(",", 2)
        if len(params_list) < 3: # The received data is not a complete frame
            return
        topic_id = params_list[0]
        data_len = params_list[1]
        msg_data = params_list[2]
        pub_topic_id_list = self.__get_pub_topic_id_list()
        if int(data_len) > len(msg_data):  # The received data is not a complete frame
            return
        elif int(data_len) < len(msg_data): # The received data may contain part of the data of another frame
            if topic_id in pub_topic_id_list:
                self.__send_to_cloud_data.append((topic_id, msg_data[:int(data_len)]))
                # Frame format: <topic_id>,<data_len>,<data>
                frame_len = len(topic_id)+len(data_len)+int(data_len)+2
                self.__parse_data = self.__parse_data[frame_len:]
                self.__parse()
            else:
                self.__parse_data = "" # Read data format eroor,restart read
                return
        else:
            self.__parse_data = ""
            if topic_id in pub_topic_id_list:
                self.__send_to_cloud_data.append((topic_id, msg_data))
            else:
                return

    def __mqtt_protocol_uart_data_parse(self, data):
        """When cloud is mqtt protocol, parse uart data.

        Args:
            data (str): Data read from uart

        Returns:
            list: topic_id and data tuple list
        """
        self.__parse_data += data
        self.__send_to_cloud_data = []
        self.__parse()

    def __send_mqtt_data(self, data):
        for send_data in data:
            self.__remote_post_data(data=send_data[1], topic_id=send_data[0])
            utime.sleep_ms(10)

    def __uplink_data(self, data):
        """Parsing uart data, send data to cloud

        Args:
            data (bytes): data read from uart
        """
        gui_tool_ack = self.__gui_tools_interac.parse_serial_data(data)
        if gui_tool_ack: # GUI tools command data
            self.__serial.write(gui_tool_ack)
            return

        if settings.current_settings["system_config"]["cloud"] == "tcp_private_cloud":
            self.__remote_post_data(data=data)
        else:
            try:
                self.__mqtt_protocol_uart_data_parse(data)
                if len(self.__send_to_cloud_data) != 0:
                    _thread.start_new_thread(self.__send_mqtt_data, (self.__send_to_cloud_data,))
            except Exception as e:
                log.error(e)

    def __post_history_data(self, data):
        """Post history data to cloud

        Args:
            data (str): history data

        Returns:
            True: Successfully post
            False:Failure to post
        """
        log.info("post_history_data")
        try:
            if settings.current_settings["system_config"]["cloud"] == "tcp_private_cloud_config":
                return self.__remote_post_data(data=data)
            else:
                # In this case, topic id is not used specified, topic id default 0.
                return self.__remote_post_data(data=data, topic_id=0)
        except Exception as e:
            log.error(e)
            return False

    def add_module(self, module, callback=None):
        if isinstance(module, RemotePublish):
            self.__remote_pub = module
            return True
        elif isinstance(module, Serial):
            self.__serial = module
            return True
        elif isinstance(module, History):
            self.__history = module
            return True
        elif isinstance(module, GuiToolsInteraction):
            self.__gui_tools_interac = module
            return True
        return False

    def uplink_main(self):
        """Read serial data, parse and upload to the cloud
        """
        while 1:
            # Read uart data
            read_byte = self.__serial.read(nbytes=1024, timeout=100)
            if read_byte:
                try:
                    self.__uplink_data(read_byte)
                except Exception as e:
                    usys.print_exception(e)
                    log.error("Parse uart data error: %s" % e)
  
    def report_history(self):
        """Report history data to cloud
        Returns:
            boolen: True: Successfully post
                    False:Failure to post
        """
        if not self.__history:
            raise TypeError("self.__history is not registered.")

        res = True
        hist = self.__history.read()
        print("hist[data]:", hist["data"])

        if hist["data"]:
            pt_count = 0
            for i, data in enumerate(hist["data"]):
                pt_count += 1
                if not self.__post_history_data(data):
                    res = False
                    break

            hist["data"] = hist["data"][pt_count:]
            if hist["data"]:
                # Flush data in hist-dictionary to tracker_data.hist file.
                self.__history.write(hist["data"])

        return res



class GuiToolsInteraction():
    def __init__(self):
        self.__query_command = {
            0: "get_imei",
            1: "get_number",
            2: "get_csq",
            3: "get_cur_config",
            4: "get_iccid",
        }
        self.__basic_setting_command = {
            255: "restart",
            50: "set_fota",
            51: "set_sota",
            52: "set_history_data",
            53: "set_uart_conf",
            54: "set_cloud_conf",
            55: "retore_factory_setting",
        }

    def __get_imei(self, code, data):
        return {"code": code, "data": modem.getDevImei(), "status": 1}

    def __get_number(self, code, data):
        log.info(sim.getPhoneNumber())
        return {"code": code, "data": sim.getPhoneNumber(), "status": 1}

    def __get_csq(self, code, data):
        return {"code": code, "data": net.csqQueryPoll(), "status": 1}

    def __get_cur_config(self, code, data):
        log.info("get_cur_config")
        current_settings = settings.get()
        return {"code": code, "data": current_settings, "status": 1}

    def __restart(self, code, data):
        log.info("Restarting...")
        Power.powerRestart()

    def __set_fota(self, code, data):
        try:
            settings.set("fota", data["fota"])
            settings.save()
            return {"code": code, "status": 1}
        except Exception as e:
            log.error("e = {}".format(e))
            return {"code": code, "status": 0}

    def __set_sota(self, code, data):
        try:
            settings.set("sota", data["sota"])
            settings.save()
            return {"code": code, "status": 1}
        except Exception as e:
            log.error("e = {}".format(e))
            return {"code": code, "status": 0}

    def __set_history_data(self, code, data):
        try:
            settings.set("offline_storage", data["offline_storage"])
            settings.save()
            return {"code": code, "status": 1}
        except Exception as e:
            log.error("e = {}".format(e))
            return {"code": code, "status": 0}
    
    def __set_uart_conf(self, code, data):
        try:
            uart_conf = data["uart_config"]
            if not isinstance(uart_conf, dict):
                raise Exception("Data type error")
            settings.set("uart_config", uart_conf)
            settings.save()
            return {"code": code, "status": 1}
        except Exception as e:
            log.error("e = {}".format(e))
            return {"code": code, "status": 0}

    def __set_cloud_conf(self, code, data):
        try:
            cloud_type = data["cloud_type"]
            cloud_conf = data["cloud_conf"]
            if not isinstance(cloud_conf, dict):
                raise Exception("Data type error")
            settings.set(cloud_type+"_config", cloud_conf)
            settings.set("cloud", cloud_type)
            settings.save()
            return {"code": code, "status": 1}
        except Exception as e:
            log.error("e = {}".format(e))
            return {"code": code, "status": 0}
    
    def __retore_factory_setting(self, code, data):
        try:
            settings.reset()
            Power.powerRestart()
            return {"code": code, "status": 1}
        except Exception as e:
            log.error("e = {}".format(e))
            return {"code": code, "status": 0}

    def __exec_command_code(self, cmd_code, data=None):
        if cmd_code in self.__query_command.keys():
            try:
                cmd = "__" + self.__query_command.get(cmd_code)
                func = getattr(self, cmd)
                ret = func(cmd_code, data)
            except Exception as e:
                log.error("search_command_func_code_list:", e)
        elif cmd_code in self.__basic_setting_command.keys():
            try:
                cmd = "__" + self.__basic_setting_command.get(cmd_code)
                func = getattr(self, cmd)
                ret = func(cmd_code, data)
            except Exception as e:
                log.error("basic_setting_command_list:", e)
        else:
            log.error("Command code error")
            ret = {"code": cmd_code, "status": 0, "error": "Command code error"}
        return ret

    def parse_serial_data(self, serial_data):
        """Parse uart data in the format specified by the GUI

        Args:
            gui_data (bytes): data read from uart
            sid (str): uart channel id

        Returns:
            True: GUI data was successfully obtained
            False: get GUI data failed
        """
        print("serial data:", serial_data)
        data_list = serial_data.split(",", 2)
        if len(data_list) != 3:
            log.info("DTU CMD list length validate fail. CMD Parse end.")
            return ""
        gui_code = data_list[0]
        if gui_code != "99":
            return ""
        data_length = data_list[1]
        msg_data = data_list[2]
        try:
            data_len_int = int(data_length)
        except:
            log.error("DTU CMD data error.")
            return ""
        if len(msg_data) > data_len_int:
            log.error("DTU CMD length validate failed.")
            return ""
        elif len(msg_data) < data_len_int:
            log.info("Msg length shorter than length")
            return ""
        try:
            data = ujson.loads(msg_data)
        except Exception as e:
            log.error(e)
            return ""
        cmd_code = data.get("cmd_code")
        # No command code was obtained
        if cmd_code is None:
            return ""
        params_data = data.get("data")
        rec = self.__exec_command_code(int(cmd_code), data=params_data)
        rec_str = ujson.dumps(rec)
        rec_format = "99,{},{}".format(len(rec_str), rec_str)
        print("GUI CMD SUCCESS")
        return rec_format
    