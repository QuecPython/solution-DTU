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
@file      :command_modbus_mode.py
@author    :elian.wang@quectel.com
@brief     :Dtu function interface that works in command mode
@version   :0.1
@date      :2022-05-20 16:32:51
@copyright :Copyright (c) 2022
"""

import net
import sim
import sms
import log
import ujson
import audio
import modem
import ntptime
import ubinascii
import cellLocator

from misc import Power, ADC
from usr.dtu_gpio import Gpio
from usr.settings import settings
from usr.modules.logging import getLogger
from usr.modules.common import Singleton
from usr.settings import PROJECT_VERSION
from usr.dtu_crc import dtu_crc
from usr.modules.temp_humidity_sensor import TempHumiditySensor

log = getLogger(__name__)

dev_imei = modem.getDevImei()
HISTORY_ERROR = []


def modbus_crc(bytearray_data):
    crc = 0xFFFF
    for pos in bytearray_data:
        crc ^= pos
        for i in range(8):
            if ((crc & 1) != 0):
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1
    gen_crc = hex(((crc & 0xff) << 8) + (crc >> 8))
    int_crc = int(gen_crc, 16)
    high, low = divmod(int_crc, 0x100)
    bytearray_data.append(high)
    bytearray_data.append(low)
    return bytearray_data

class DTUSearchCommand(Singleton):
    def __init__(self):
        self.__channel = None

    def set_channel(self, channel):
        self.__channel = channel

    def get_imei(self, code, data):
        return {"code": code, "data": modem.getDevImei(), "status": 1}

    def get_number(self, code, data):
        log.info(sim.getPhoneNumber())
        return {"code": code, "data": sim.getPhoneNumber(), "status": 1}

    def get_version(self, code, data):
        log.info(PROJECT_VERSION)
        return {"code": code, "data": PROJECT_VERSION, "status": 1}

    def get_csq(self, code, data):
        return {"code": code, "data": net.csqQueryPoll(), "status": 1}

    def get_cur_config(self, code, data):
        log.info("get_cur_config")
        current_settings = settings.get()
        return {"code": code, "data": current_settings, "status": 1}

    def get_diagnostic_info(self, code, data):
        log.info("get_diagnostic_message")
        return {"code": code, "data": str(HISTORY_ERROR), "status": 1}

    def get_iccid(self, code, data):
        log.info("get_iccid")
        return {"code": code, "data": sim.getIccid(), "status": 1}

    def get_adc(self, code, data):
        log.info("get_adc")
        try:
            adc = ADC()
            adc.open()
            adcn_val = "ADC%s" % str(data.get("adcn", 0))
            adcn = getattr(ADC, adcn_val)
            adcv = adc.read(adcn)
            adc.close()
        except Exception as e:
            log.error(e)
            return {"code": code, "data": None, "status": 0}
        else:
            adc.close()
            return {"code": code, "data": adcv, "status": 1}

    def get_gpio(self, code, data):
        log.info("get_gpio")
        try:
            pins = data["pins"]
            prod_gpio = Gpio("")
            gpio_get = getattr(prod_gpio, "gpio%s" % pins)
            gpor_read = gpio_get.read()
        except Exception as e:
            log.error("get gpio err:",e)
            return {"code": code, "status": 0}
        else:
            return {"code": code, "data": gpor_read, "status": 1}

    def get_vbatt(self, code, data):
        log.info("get_vbatt")
        return {"code": code, "data": Power.getVbatt(), "status": 1}

    def get_temp_humid(self, code, data):
        log.info("get_temp_humid")
        sensor_th = TempHumiditySensor()
        temp, humid = sensor_th.read()
        return {"code": code, "data": {"temperature": temp, "humidity": humid}, "status": 1}

    def get_network_connect(self, code, data):
        log.info("get_network_connect")
        conn_status = dict()
        for code, connect in self.__channel.cloud_object_dict.items():
            if connect.get_status() == True:
                conn_status[code] = 1
            else:
                conn_status[code] = 0
        return {"code": code, "data": conn_status, "status": 1}

    def get_cell_status(self, code, data):
        log.info("get_cell_status")
        states = net.getState()
        states_dict = {
            "voice_state": states[0][0],
            "data_state": states[1][0]
        }
        return {"code": code, "data": states_dict, "status": 1}

    def get_celllocator(self, code, data):
        log.info("get_celllocator")
        res = cellLocator.getLocation("www.queclocator.com", 80, "xGP77d2z0i91s67n", 8, 1)
        if res == (0.0, 0.0, 0):
            return {"code": code, "data": {}, "status": 0}
        else:
            return {"code": code, "data": {"latitude": res[0], "longitude": res[1]}, "status": 1}


class BasicSettingCommand(Singleton):
    def restart(self, code, data):
        log.info("Restarting...")
        Power.powerRestart()

    def set_reg(self, code, data):
        try:
            settings.set("reg", data["reg"])
            settings.save()
            return {"code": code, "status": 1}
        except Exception as e:
            log.error("e = {}".format(e))
            return {"code": code, "status": 0}
    
    def set_parameter_version(self, code, data):
        try:
            settings.set("version", data["version"])
            settings.save()
            return {"code": code, "status": 1}
        except Exception as e:
            log.error("e = {}".format(e))
            return {"code": code, "status": 0}

    def set_passwd(self, code, data):
        print("set_passwd")
        try:
            print("new_password:", data.get("new_password"))
            settings.set("password", str(data["new_password"]))
            log.info("new password:", settings.current_settings.get("password"))
            settings.save()
            return {"code": code, "status": 1}
        except Exception as e:
            log.error("e = {}".format(e))
            return {"code": code, "status": 0}

    def set_fota(self, code, data):
        try:
            settings.set("fota", data["fota"])
            settings.save()
            return {"code": code, "status": 1}
        except Exception as e:
            log.error("e = {}".format(e))
            return {"code": code, "status": 0}

    def set_ota(self, code, data):
        try:
            settings.set("ota", data["ota"])
            settings.save()
            return {"code": code, "status": 1}
        except Exception as e:
            log.error("e = {}".format(e))
            return {"code": code, "status": 0}

    def set_nolog(self, code, data):
        try:
            settings.set("nolog", data["nolog"])
            settings.save()
            return {"code": code, "status": 1}
        except Exception as e:
            log.error("e = {}".format(e))
            return {"code": code, "status": 0}

    def set_service_acquire(self, code, data):
        try:
            settings.set("service_acquire", data["service_acquire"])
            settings.save()
            return {"code": code, "status": 1}
        except Exception as e:
            log.error("e = {}".format(e))
            return {"code": code, "status": 0}

    def set_uconf(self, code, data):
        try:
            uconf = data["uconf"]
            if not isinstance(uconf, dict):
                raise Exception("Data type error")
            settings.set("uconf", uconf)
            settings.save()
            return {"code": code, "status": 1}
        except Exception as e:
            log.error("e = {}".format(e))
            return {"code": code, "status": 0}

    def set_dtu_conf(self, code, data):
        try:
            conf = data["conf"]
            if not isinstance(conf, dict):
                raise Exception("Data type error")
            settings.set("conf", conf)
            settings.save()
            return {"code": code, "status": 1}
        except Exception as e:
            log.error(e)
            return {"code": code, "status": 0}
            

    def set_apns(self, code, data):
        print("apn_code_data: ", code, data)
        try:
            apn = data["apn"]
            if not isinstance(apn, list):
                raise Exception("Data type error")
            if len(apn) != 3:
                raise Exception("Params number error")
            settings.set("apn", apn)
            settings.save()
            return {"code": code, "status": 1}
        except Exception as e:
            log.error(e)
            return {"code": code, "status": 0}
            

    def set_pins(self, code, data):
        print("pins_code_data: ", code, data)
        try:
            pins = data["pins"]
            if not isinstance(pins, list):
                raise Exception("Data type error")
            settings.set("pins", pins)
            settings.save()
            return {"code": code, "status": 1}
        except Exception as e:
            log.error(e)
            return {"code": code, "status": 0}

    def set_params(self, code, data):
        try:
            conf = data["dtu_config"]
            if not isinstance(conf, dict):
                raise Exception("Data type error")
            if settings.set_multi(conf):
                return {"code": code, "status": 1}
            else:
                return {"code": code, "status": 0}
        except Exception as e:
            log.error(e)
            return {"code": code, "status": 0}

    def set_tts(self, code, data):
        print("tts_code_data: ", code, data)
        try:
            device = data["device"]
            tts = audio.TTS(device)
            tts.play(4, 0, 2, str(data["string"]))
        except Exception as e:
            log.error(e)
            return {"code": code, "status": 0}
        else:
            return {"code": code, "status": 1}

    def set_ntp(self, code, data):
        print("ntp_code_data: ", code, data)
        ntp_server = data.get("ntp_server", None)
        if ntp_server:
            try:
                ntptime.sethost(ntp_server)
            except Exception as e:
                return {"code": code, "status": 0}
        try:
            ntptime.settime()
        except Exception as e:
            log.error(e)
            return {"code": code, "status": 0}
        return {"code": code, "status": 1}

    def set_message(self, code, data):
        print("set_message")
        try:
            number = data["number"]
            msg = data["sms_msg"]
            if sms.sendTextMsg(number, msg, 'GSM') == 0:
                return {"code": code, "status": 1}
            else:
                return {"code": code, "status": 0}
        except Exception as e:
            log.error(e)
            return {"code": code, "status": 0}
        

class CommandModbusMode(Singleton):
    """When working in command mode, the DTU receives cloud data and serial port data
    """
    def __init__(self):
        self.__not_need_password_verify_code = [0x00, 0x01, 0x02, 0x03, 0x05]
        self.__search_command = {
            0: "get_imei",
            1: "get_number",
            2: "get_version",
            3: "get_csq",
            4: "get_cur_config",
            5: "get_diagnostic_info",
            6: "get_iccid",
            7: "get_adc",
            8: "get_gpio",
            9: "get_vbatt",
            10: "get_temp_humid",
            11: "get_network_connect",
            12: "get_cell_status",
            13: "get_celllocator",
        }
        self.__basic_setting_command = {
            255: "restart",
            50: "set_message",
            51: "set_passwd",
            53: "set_reg",
            54: "set_parameter_version",
            55: "set_fota",
            56: "set_nolog",
            57: "set_service_acquire",
            58: "set_uconf",
            59: "set_dtu_conf",
            60: "set_apns",
            61: "set_pins",
            62: "set_ota",
            63: "set_params",
            64: "set_tts",
            65: "set_ntp",
        }
        self.__search_command_func_code_list = self.__search_command.keys()
        self.__basic_setting_command_list = self.__basic_setting_command.keys()
        self.search_cmd = DTUSearchCommand()
        self.__setting_cmd = BasicSettingCommand()
        self.__groups = dict()
        current_settings = settings.get()
        groups_conf = current_settings.get("modbus").get("groups", [])
        idx = 0
        for group in groups_conf:
            self.__groups[idx] = [int(x, 16) for x in group["slave_address"]]
            idx += 1

    def __package_datas(self, msg_data, topic_id=None, channel_id=None):
        """Package downsteam data

        Args:
            msg_data (str): Data that needs to be send
            topic_id (str): Topic id of data to be sent.
            channel_id (str): Channel id of data to be sent.

        Returns:
            bytes: Complete the packaged data
        """
        if msg_data is not None:
            msg_length = len(str(msg_data))
            crc32_val = dtu_crc.crc32(str(msg_data))
            if topic_id == None: # tcp\udp
                ret_bytes = "%s,%s,%s,%s".encode('utf-8') % (str(channel_id), str(msg_length), str(crc32_val), str(msg_data))
            else:
                ret_bytes = "%s,%s,%s,%s,%s".encode('utf-8') % (str(channel_id), str(topic_id), str(msg_length), str(crc32_val), str(msg_data))
        else:
            ret_bytes = None

        print("ret_bytes:", ret_bytes)
        return ret_bytes
    def exec_command_code(self, cmd_code, data=None, password=None):
        """Execute external command code and return execution results

        Args:
            cmd_code (int): dtu receive external command code
            data (str): data
            password (str): Some commands require password checks.

        Returns:
            dict: result of execute external command
        """
        ret = dict()
        #check password
        if cmd_code not in self.__not_need_password_verify_code:
            if password != settings.current_settings.get("password"):
                log.error("Password verify error")
                ret = {"code": cmd_code, "status": 0, "error": "Password verify error"}
                return ret

        print("cmd_code", cmd_code)
        if cmd_code in self.__search_command_func_code_list:
            try:
                cmd_str = self.__search_command.get(cmd_code)
                func = getattr(self.search_cmd, cmd_str)
                ret = func(cmd_code, data)
            except Exception as e:
                log.error("search_command_func_code_list:", e)
        elif cmd_code in self.__basic_setting_command_list:
            try:
                cmd_str = self.__basic_setting_command.get(cmd_code)
                func = getattr(self.__setting_cmd, cmd_str)
                ret = func(cmd_code, data)
            except Exception as e:
                log.error("basic_setting_command_list:", e)
        else:
            log.error("Command code error")
            ret = {"code": cmd_code, "status": 0, "error": "Command code error"}
        return ret

    def cloud_data_parse(self, data, topic_id, channel_id):
        """Dtu parse cloud data,return cloud data or serial data

        Args:
            data (str): cloud publish data
            topic_id (str): toic id of data
            channel_id (str): cloud channel id 

        Returns:
            dict: Data that has been processed,wait to send to cloud or uart
        """

        ret_data = {"cloud_data":None, "uart_data":None}
        try:
            if isinstance(data, str):
                msg_data = ujson.loads(data)
            else:
                raise Exception("Cloud data parse error")
        except Exception as e:
            log.info(e)
            return ret_data

        cmd_code = msg_data.get("cmd_code", None)
        msg_id = msg_data.get("msg_id", None)
        password = msg_data.get("password", None)
        cloud_request_topic = msg_data.get("topic_id", None)
        data = msg_data.get("data", None)
        modbus_data = msg_data.get("modbus", None)

        # commond mode 
        if cmd_code is not None:
            ret_data["cloud_data"] = self.exec_command_code(int(cmd_code), data=data, password=password)
            # The "msg_id" in the reply packet is the same as the "msg_id" sent by the cloud
            ret_data["cloud_data"]["msg_id"] = msg_id

            # Determine whether the topic of the reply message is specified in the cloud instruction
            if cloud_request_topic is not None:
                ret_data["cloud_data"]["topic_id"] = cloud_request_topic
            
            return ret_data
        elif modbus_data is not None: # modbus mode
            if "groups" in modbus_data:
                groups_num = modbus_data["groups"].get("num")
                cmd = modbus_data["groups"].get("cmd")
                try:
                    int_cmd = [int(x, 16) for x in cmd]
                except Exception as e:
                    log.info("modbus command error: %s" % e)
                    ret_data["cloud_data"] = {"status": 0, "error": e}
                groups_addr = self.__groups.get(int(groups_num))
                for addr in groups_addr:
                    modbus_cmd = [addr]
                    modbus_cmd.extend(int_cmd)
                    crc_cmd = modbus_crc(bytearray(modbus_cmd))
                    print(crc_cmd)
                    ret_data["uart_data"] = crc_cmd
                ret_data["cloud_data"] = {"code": cmd, "status": 1}
            elif "command" in data:
                command = modbus_data["command"]
                try:
                    int_cmd = [int(x, 16) for x in command]
                    crc_cmd = modbus_crc(bytearray(int_cmd))
                except Exception as e:
                    log.info("modbus command error: %s" % e)
                    ret_data["cloud_data"] = {"status": 0, "error": e}
                ret_data["uart_data"] = crc_cmd
                ret_data["cloud_data"] = {"code": command, "status": 1}
            else:
                err_msg = "can't get any modbus params"
                log.error("Modbus mode: can't get any modbus params")
                ret_data["cloud_data"] = {"code": 0, "status": 0, "error": err_msg}
            return ret_data
        else:
            ret_data["uart_data"] = self.__package_datas(data, topic_id, channel_id)
            return ret_data
        

    def uart_data_parse(self, data, cloud_channel_dict, cloud_channel_array=None):
        """Parse the data read from uart

        Args:
            data (bytes): Data read from the serial port
            cloud_channel_dict (dict): cloud config dict 
            cloud_channel_array(list): Cloud channel list corresponding to uart channel 
        Returns:
            list: 1.msg_data:Data that has been processed,wait to send to cloud
                  2.cloud_channel_id:cloud channel id 
                  3.topic_id:toic id of data
        """
        if "," not in data.decode():
            work_mode = "modbus"
        else:
            if modbus_crc(bytearray(data))[-2:-1] == bytearray(b'\x00'):
                work_mode = "modbus"
            else:
                work_mode = "cmd"
        # In Modbus mode, one Uart port corresponds to one cloud channel
        # In Command mode, one Uart port can corresponds to multi cloud channel
        if work_mode == "cmd":
            channel_id = data.decode().split(",")[0]
            if channel_id not in cloud_channel_array:
                log.error("Channel id not exist. Check conf config.")
                return []
        else: 
            channel_id = cloud_channel_array[0]
        channel = cloud_channel_dict.get(str(channel_id))
        if not channel:
            log.error("Channel id not exist. Check serialID config.")
            return False, []

        if work_mode == "cmd":
            if channel.get("protocol") in ["tcp", "udp"]:
                # According to different protocols, it is divided into lists of different lengths
                params_list = data.decode().split(",", 3)
                msg_len = params_list[1]
                if msg_len == "0":
                    return [{}, channel_id]
                else:
                    crc32 = params_list[2]
                    msg_data = params_list[3]
                    try:
                        msg_len_int = int(msg_len)
                    except:
                        log.error("data parse error")
                        return []
                    # Message length check
                    if msg_len_int != len(msg_data):
                        return []
                    cal_crc32 = dtu_crc.crc32(msg_data)
                    if cal_crc32 == crc32:
                        return [ujson.dumps({"data": msg_data}), channel_id]
                    else:
                        log.error("crc32 error")
                        return []
            else:
                # According to different protocols, it is divided into lists of different lengths
                params_list = data.decode().split(",", 4)
                topic_id = params_list[1]
                msg_len = params_list[2]
                if msg_len == "0":
                    return [{}, channel_id]
                else:
                    crc32 = params_list[3]
                    msg_data = params_list[4]
                    try:
                        msg_len_int = int(msg_len)
                    except:
                        log.error("data parse error")
                        return []
                    # Message length check
                    if msg_len_int != len(msg_data):
                        return []
                    cal_crc32 = dtu_crc.crc32(msg_data)
                    if crc32 == cal_crc32:
                        return [ujson.dumps({"data": msg_data}), channel_id, topic_id]
                    else:
                        return []
        else:
            modbus_data_list = ubinascii.hexlify(data, ",").decode().split(",")
            hex_str_list = ["0x" + x for x in modbus_data_list]
            # 返回channel
            if channel.get("protocol") in ["http", "tcp", "udp", "quecthing"]:
                return [str(hex_str_list), channel_id]
            else:
                topics = list(channel.get("publish").keys())
                return [str(hex_str_list), channel_id, topics[0]]