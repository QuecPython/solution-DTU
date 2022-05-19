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


import net
import sim
import sms
import log
import ujson
import audio
import modem
import ntptime
import cellLocator
from usr.modules.common import Singleton
from misc import Power, ADC
from usr.t_h import SensorTH
from usr.dtu_gpio import Gpio
from usr.modules.logging import getLogger
from usr.modules.logging import RET
from usr.modules.logging import error_map
from usr.modules.logging import DTUException
from usr.settings import PROJECT_NAME, PROJECT_VERSION, DEVICE_FIRMWARE_NAME, DEVICE_FIRMWARE_VERSION
from usr.settings import settings

log = getLogger(__name__)

dev_imei = modem.getDevImei()
HISTORY_ERROR = []

class DTUSearchCommand(Singleton):
    def __init__(self):
        self.__channel = None

    def set_channel(self, channel):
        self.__channel = channel

    def get_imei(self, code, data):
        return {"code": code, "data": dev_imei, "status": 1}

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
            adcn_val = "ADC%s" % str(data["adcn"])
            adcn = getattr(ADC, adcn_val)
            adcv = adc.read(adcn)
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
            prod_gpio = Gpio()
            gpio_get = getattr(prod_gpio, "gpio%s" % pins)
            gpor_read = gpio_get.read()
        except DTUException as e:
            log.error(e)
            return {"code": code, "status": 0}
        except Exception as e:
            log.error(e)
            return {"code": code, "status": 0}
        else:
           return {"code": code, "data": gpor_read, "status": 1}

    def get_vbatt(self, code, data):
        log.info("get_vbatt")
        return {"code": code, "data": Power.getVbatt(), "status": 1}

    def get_temp_humid(self, code, data):
        log.info("get_temp_humid")
        sensor_th = SensorTH()
        temp, humid = sensor_th.read()
        return {"code": code, "data": {"temperature": temp, "humidity": humid}, "status": 1}

    def get_network_connect(self, code, data):
        log.info("get_network_connect")
        conn_status = dict()
        for code, connect in self.__channel.cloud_object_dict.items():
            conn_status[code] = connect.get_status()
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
        res = cellLocator.getLocation("www.queclocator.com", 80, "1111111122222222", 8, 1)
        location_dict = {
            "latitude": res[0],
            "longitude": res[1],
        }
        return {"code": code, "data": location_dict, "status": 1}


class BasicSettingCommand(Singleton):
    def restart(self, code, data):
        log.info("Restarting...")
        Power.powerRestart()

    def set_plate(self, code, data):
        try:
            settings.set("plate", data["plate"])
            settings.save()
            return {"code": code, "status": 1}
        except Exception as e:
            log.error("e = {}".format(e))
            return {"code": code, "status": 0}

    def set_reg(self, code, data):
        try:
            settings.set("reg", data["reg"])
            settings.save()
            return {"code": code, "status": 1}
        except Exception as e:
            log.error("e = {}".format(e))
            return {"code": code, "status": 0}

    def set_version(self, code, data):
        try:
            settings.set("version", data["version"])
            settings.save()
            return {"code": code, "status": 1}
        except Exception as e:
            log.error("e = {}".format(e))
            return {"code": code, "status": 0}

    def set_passwd(self, code, data):
        try:
            settings.set("password", str(data["new_password"]))
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
                raise DTUException(RET.DATATYPEERR)
            settings.set("uconf", uconf)
            settings.save()
            return {"code": code, "status": 1}
        except DTUException as e:
            log.error(e)
            return {"code": code, "status": 0}
        except Exception as e:
            log.error("e = {}".format(e))
            return {"code": code, "status": 0}

    def set_dtu_conf(self, code, data):
        try:
            conf = data["conf"]
            if not isinstance(conf, dict):
                raise DTUException(RET.DATATYPEERR)
            settings.set("conf", conf)
            settings.save()
            return {"code": code, "status": 1}
        except DTUException as e:
            log.error(e)
            return {"code": code, "status": 0}
        except Exception as e:
            log.error(e)
            return {"code": code, "status": 0}
            

    def set_apns(self, code, data):
        print("apn_code_data: ", code, data)
        try:
            apn = data["apn"]
            if not isinstance(apn, list):
                raise DTUException(RET.DATATYPEERR)
            if len(apn) != 3:
                raise DTUException(RET.NUMBERERR)
            settings.set("apn", apn)
            settings.save()
            return {"code": code, "status": 1}
        except DTUException as e:
            log.error(e)
            return {"code": code, "status": 0}
        except Exception as e:
            log.error(e)
            return {"code": code, "status": 0}
            

    def set_pins(self, code, data):
        print("pins_code_data: ", code, data)
        try:
            pins = data["pins"]
            if not isinstance(pins, list):
                raise DTUException(RET.DATATYPEERR)
            settings.set("pins", pins)
            settings.save()
            return {"code": code, "status": 1}
        except DTUException as e:
            log.error(e)
            return {"code": code, "status": 0}
        except Exception as e:
            log.error(e)
            return {"code": code, "status": 0}

    def set_params(self, code, data):
        try:
            conf = data["dtu_config"]
            if not isinstance(conf, dict):
                raise DTUException(RET.DATATYPEERR)
            if settings.set_multi(conf):
                return {"code": code, "status": 1}
            else:
                return {"code": code, "status": 0}
        except DTUException as e:
            log.error(e)
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
            sms.sendTextMsg(number, msg, "UCS2")
        except Exception as e:
            log.error(e)
            return {"code": code, "status": 0}
        return {"code": code, "status": 1}

class CommandMode(Singleton):

    def __init__(self):
        self.__not_need_password_verify_code = [0x00, 0x01, 0x02, 0x03, 0x05]
        self.search_command = {
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
        self.basic_setting_command = {
            255: "restart",
            50: "set_message",
            51: "set_passwd",
            52: "set_plate",
            53: "set_reg",
            54: "set_version",
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
        self.search_command_func_code_list = self.search_command.keys()
        self.basic_setting_command_list = self.basic_setting_command.keys()
        self.__protocol = None
        self.search_cmd = DTUSearchCommand()
        self.setting_cmd = BasicSettingCommand()

    def set_protocol(self, protocol):
        self.__protocol = protocol

    def cloud_data_parse(self, data, topic_id, channel_id):
        ret_data = {"cloud_data":None, "uart_data":None}
        print("data:", data)
        print("type data:", type(data))
        try:
            if isinstance(data, str):
                msg_data = ujson.loads(data)
            elif isinstance(data, bytes):
                msg_data = ujson.loads(str(data))
            elif isinstance(data, dict):
                msg_data = data
            else:
                raise error_map.get(RET.CMDPARSEERR)
        except Exception as e:
                log.info(e)

        cmd_code = msg_data.get("cmd_code", None)
        msg_id = msg_data.get("msg_id")
        password = msg_data.get("password", None)
        cloud_request_topic = msg_data.get("topic_id", None)
        data = msg_data.get("data", None)

        if cmd_code is not None:
            if cmd_code not in self.__not_need_password_verify_code:
                if password != settings.current_settings.get("password"):
                    log.error(error_map.get(RET.PASSWDVERIFYERR))
                    ret_data["cloud_data"] = {"code": cmd_code, "status": 0, "error": error_map.get(RET.PASSWDVERIFYERR)}

            print("cmd_code", cmd_code)
            if cmd_code in self.search_command_func_code_list:
                try:
                    cmd_str = self.search_command.get(cmd_code)
                    func = getattr(self.search_cmd, cmd_str)
                    ret_data["cloud_data"] = func(cmd_code, msg_data)
                except Exception as e:
                    log.error("search_command_func_code_list:", e)
            elif cmd_code in self.basic_setting_command_list:
                try:
                    cmd_str = self.basic_setting_command.get(cmd_code)
                    func = getattr(self.setting_cmd, cmd_str)
                    ret_data["cloud_data"] = func(cmd_code, data)
                except Exception as e:
                    log.error("basic_setting_command_list:", e)
            else:
                # err
                log.error(error_map.get(RET.POINTERR))
                ret_data["cloud_data"] = {"code": cmd_code, "status": 0, "error": error_map.get(RET.POINTERR)}

            # 应答报文中msg_id与 云端发送的msg_id保持一致
            ret_data["cloud_data"]["msg_id"] = msg_id

            # 判断云端指令中是否指定应答报文的topic
            if cloud_request_topic is not None:
                ret_data["cloud_data"]["topic_id"] = cloud_request_topic
            
            return ret_data
        else:
            package_data = self.__protocol.package_datas(data, topic_id, channel_id)
            ret_data["uart_data"] = package_data
            return ret_data
        

    def uart_data_parse(self, data, cloud_channel_dict, cloud_channel_array=None):
        str_msg = data.decode()
        params_list = str_msg.split(",")
        if len(params_list) not in [2, 4, 5]:
            log.error("param length error")
            return False, []

        channel_id = params_list[0]
        if channel_id not in cloud_channel_array:
            log.error("Channel id not exist. Check conf config.")
            return False, []
            
        channel = cloud_channel_dict.get(str(channel_id))
        if not channel:
            log.error("Channel id not exist. Check serialID config.")
            return False, []
        if channel.get("protocol") in ["http", "tcp", "udp"]:
            msg_len = params_list[1]
            if msg_len == "0":
                return {}, [channel_id]
            else:
                crc32 = params_list[2]
                msg_data = params_list[3]
                try:
                    msg_len_int = int(msg_len)
                except:
                    log.error("data parse error")
                    return False, []
                valid_rec = self.__protocol.validate_length(msg_len_int, msg_data, str_msg)
                if not valid_rec:
                    return False, []
                cal_crc32 = self.__protocol.crc32(msg_data)
                if cal_crc32 == crc32:
                    return {"data": msg_data}, [channel_id]
                else:
                    log.error("crc32 error")
                    return False, []
        else:
            topic_id = params_list[1]
            msg_len = params_list[2]
            crc32 = params_list[3]
            msg_data = params_list[4]
            try:
                msg_len_int = int(msg_len)
            except:
                log.error("data parse error")
                return False, []
            # 加入buffer
            valid_rec = self.__protocol.validate_length(msg_len_int, msg_data, str_msg)
            if not valid_rec:
                return False, []
            cal_crc32 = self.__protocol.crc32(msg_data)
            if crc32 == cal_crc32:
                return {"data": msg_data}, [channel_id, topic_id]
            else:
                return False, []