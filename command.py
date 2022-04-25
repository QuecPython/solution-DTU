import ujson
import ntptime
import net
import sim
import sms
import audio
import log
import modem
import cellLocator
import utime
from usr.singleton import Singleton
from misc import Power, ADC
from usr.t_h import SensorTH
from usr.settings import DTUDocumentData
#from usr.dtu_handler import ProdDtu
from usr.dtu_log import DTUException
from usr.dtu_log import RET
from usr.dtu_log import error_map
from usr.modbus import modbus_crc
from usr.settings import CONFIG
from usr.dtu_gpio import ProdGPIO

log.basicConfig(level=log.INFO)
logger = log.getLogger(__name__)

dev_imei = modem.getDevImei()
HISTORY_ERROR = []
CHANNELS = dict()

@Singleton
class DTUSearchCommand(object):
    def __init__(self):
        self.dtu_c = DTUDocumentData()

    def get_imei(self, code, data):
        return {'code': code, 'data': dev_imei, 'status': 1}

    def get_number(self, code, data):
        logger.info(sim.getPhoneNumber())
        return {'code': code, 'data': sim.getPhoneNumber(), 'status': 1}

    def get_version(self, code, data):
        logger.info(self.dtu_c.version)
        return {'code': code, 'data': self.dtu_c.version, 'status': 1}

    def get_csq(self, code, data):
        return {'code': code, 'data': net.csqQueryPoll(), 'status': 1}

    def get_cur_config(self, code, data):
        logger.info("get_cur_config")
        return {'code': code, 'data': self.dtu_c.json_info(need=False), 'status': 1}

    def get_diagnostic_info(self, code, data):
        logger.info("get_diagnostic_message")
        return {'code': code, 'data': str(HISTORY_ERROR), 'status': 1}

    def get_iccid(self, code, data):
        logger.info("get_iccid")
        return {'code': code, 'data': sim.getIccid(), 'status': 1}

    def get_adc(self, code, data):
        logger.info("get_adc")
        try:
            adc = ADC()
            adcn_val = "ADC%s" % str(data['adcn'])
            adcn = getattr(ADC, adcn_val)
            adcv = adc.read(adcn)
        except Exception as e:
            logger.error(e)
            return {'code': code, 'data': None, 'status': 0}
        else:
            adc.close()
            return {'code': code, 'data': adcv, 'status': 1}

    def get_gpio(self, code, data):
        logger.info("get_gpio")
        try:
            pins = data["pins"]
            prod_gpio = ProdGPIO()
            gpio_get = getattr(prod_gpio, "gpio%s" % pins)
            gpor_read = gpio_get.read()
        except DTUException as e:
            logger.error(e)
            return {'code': code, 'status': 0}
        except Exception as e:
            logger.error(e)
            return {'code': code, 'status': 0}
        else:
           return {'code': code, 'data': gpor_read, 'status': 1}

    def get_vbatt(self, code, data):
        logger.info("get_vbatt")
        return {'code': code, 'data': Power.getVbatt(), 'status': 1}

    def get_temp_humid(self, code, data):
        logger.info("get_temp_humid")
        sensor_th = SensorTH()
        temp, humid = sensor_th.read()
        return {'code': code, 'data': {"temperature": temp, 'humidity': humid}, 'status': 1}

    def get_network_connect(self, code, data):
        logger.info("get_network_connect")
        channel = ChannelTransfer()
        conn_status = dict()
        for code, connect in channel.channel_dict.items():
            conn_status[code] = connect.check_net()
        return {'code': code, 'data': conn_status, 'status': 1}

    def get_cell_status(self, code, data):
        logger.info("get_cell_status")
        states = net.getState()
        states_dict = {
            "voice_state": states[0][0],
            "data_state": states[1][0]
        }
        return {'code': code, 'data': states_dict, 'status': 1}

    def get_celllocator(self, code, data):
        logger.info("get_celllocator")
        res = cellLocator.getLocation("www.queclocator.com", 80, "1111111122222222", 8, 1)
        location_dict = {
            "latitude": res[0],
            "longitude": res[1],
        }
        return {'code': code, 'data': location_dict, 'status': 1}


@Singleton
class BasicSettingCommand(object):

    def __init__(self):
        self.dtu_c = DTUDocumentData()

    def restart(self, code, data):
        logger.info("Restarting...")
        Power.powerRestart()

    def set_int_data(self, code, data, sign):
        logger.info("data: %s" % data)
        try:
            number = data[sign]
            number = int(number)
        except Exception as e:
            logger.error("e = {}".format(e))
            # self.output(code, success=0, status=RET.DATAPARSEERR)
            return {'code': code, 'status': 0}
        else:
            setattr(self.dtu_c, sign, number)
            self.dtu_c.reload_file()
            return {'code': code, 'status': 1}

    def set_plate(self, code, data):
        return self.set_int_data(code, data, 'plate')

    def set_reg(self, code, data):
        return self.set_int_data(code, data, 'reg')

    def set_version(self, code, data):
        return self.set_int_data(code, data, 'version')

    def set_passwd(self, code, data):
        try:
            passwd = str(data["new_password"])
        except Exception as e:
            logger.error("e = {}".format(e))
            return {'code': code, 'status': 0}
        else:
            setattr(self.dtu_c, "password", passwd)
            self.dtu_c.reload_file()
            return {'code': code, 'status': 1}

    def set_fota(self, code, data):
        return self.set_int_data(code, data, 'fota')

    def set_ota(self, code, data):
        print("set_ota: ", code, data)
        try:
            ota = data["ota"]
            if not isinstance(ota, list):
                raise DTUException(RET.DATATYPEERR)
            if len(ota) != 3:
                raise DTUException(RET.NUMBERERR)
        except DTUException as e:
            logger.error(e)
            return {'code': code, 'status': 0}
        except Exception as e:
            logger.error(e)
            return {'code': code, 'status': 0}
        else:
            setattr(self.dtu_c, "ota", ota)
            self.dtu_c.reload_file()
            return {'code': code, 'status': 1}

    def set_nolog(self, code, data):
        return self.set_int_data(code, data, 'nolog')

    def set_service_acquire(self, code, data):
        return self.set_int_data(code, data, 'service_acquire')

    def set_uconf(self, code, data):
        # 透传模式不能配置
        if self.dtu_c.work_mode == "through":
            return {'code': code, 'status': 0}
        try:
            uconf = data["uconf"]
            if not isinstance(uconf, dict):
                raise DTUException(RET.DATATYPEERR)
        except DTUException as e:
            logger.error(e)
            return {'code': code, 'status': 0}
        except Exception as e:
            logger.error(e)
            return {'code': code, 'status': 0}
        else:
            setattr(self.dtu_c, "uconf", uconf)
            self.dtu_c.reload_file()
            return {'code': code, 'status': 1}

    def set_dtu_conf(self, code, data):
        # 透传模式不能配置
        if self.dtu_c.work_mode == "through":
            return {'code': code, 'status': 0}
        try:
            conf = data["conf"]
            if not isinstance(conf, dict):
                raise DTUException(RET.DATATYPEERR)
        except DTUException as e:
            logger.error(e)
            return {'code': code, 'status': 0}
        except Exception as e:
            logger.error(e)
            return {'code': code, 'status': 0}
        else:
            setattr(self.dtu_c, "conf", conf)
            self.dtu_c.reload_file()
            return {'code': code, 'status': 1}

    def set_apns(self, code, data):
        # 透传模式不能配置
        if self.dtu_c.work_mode == "through":
            return {'code': code, 'status': 0}
        print("apn_code_data: ", code, data)
        self.dtu_c.apn = data
        try:
            apn = data["apn"]
            if not isinstance(apn, list):
                raise DTUException(RET.DATATYPEERR)
            if len(apn) != 3:
                raise DTUException(RET.NUMBERERR)
        except DTUException as e:
            logger.error(e)
            return {'code': code, 'status': 0}
        except Exception as e:
            logger.error(e)
            return {'code': code, 'status': 0}
        else:
            setattr(self.dtu_c, "apn", apn)
            self.dtu_c.reload_file()
            return {'code': code, 'status': 1}

    def set_pins(self, code, data):
        # 透传模式不能配置
        if self.dtu_c.work_mode == "through":
            return {'code': code, 'status': 0}
        print("pins_code_data: ", code, data)
        try:
            pins = data["pins"]
            if not isinstance(pins, list):
                raise DTUException(RET.DATATYPEERR)
            # if len(pins) != 3:
            #     raise DTUException(RET.NUMBERERR)
        except DTUException as e:
            logger.error(e)
            return {'code': code, 'status': 0}
        except Exception as e:
            logger.error(e)
            return {'code': code, 'status': 0}
        else:
            setattr(self.dtu_c, "pins", pins)
            self.dtu_c.reload_file()
            return {'code': code, 'status': 1}

    def set_params(self, code, data):
        # 透传模式不能配置
        if self.dtu_c.work_mode == "through":
            return {'code': code, 'status': 0}
        try:
            conf = data["dtu_config"]
            if not isinstance(conf, dict):
                raise DTUException(RET.DATATYPEERR)
            self.dtu_c.backup_file()
            with open(CONFIG["config_path"], mode="w") as f:
                ujson.dump(conf, f)
        except DTUException as e:
            logger.error(e)
            return {'code': code, 'status': 0}
        except Exception as e:
            logger.error(e)
            return {'code': code, 'status': 0}
        else:
            return {'code': code, 'status': 1}

    def set_tts(self, code, data):
        print("tts_code_data: ", code, data)
        try:
            device = data['device']
            tts = audio.TTS(device)
            tts.play(4, 0, 2, str(data['string']))
        except Exception as e:
            logger.error(e)
            return {'code': code, 'status': 0}
            # self.output(code, success=0, status=RET.DATAPARSEERR)
        else:
            return {'code': code, 'status': 1}
            # self.output(code)

    def set_ntp(self, code, data):
        print("ntp_code_data: ", code, data)
        ntp_server = data.get("ntp_server", None)
        if ntp_server:
            try:
                ntptime.sethost(ntp_server)
            except Exception as e:
                return {'code': code, 'status': 0}
                # logger.error(e)
        try:
            ntptime.settime()
        except Exception as e:
            logger.error(e)
            return {'code': code, 'status': 0}
            # self.output(code, success=0, status=RET.METHODERR)
        # self.output(code)
        return {'code': code, 'status': 1}

    def set_message(self, code, data):
        print("set_message")
        try:
            number = data['number']
            msg = data['sms_msg']
            sms.sendTextMsg(number, msg, "UCS2")
        except Exception as e:
            logger.error(e)
            return {'code': code, 'status': 0}
        return {'code': code, 'status': 1}

@Singleton
class ModbusCommand:

    def __init__(self, mode, modbus_conf):
        print("modbusCMD start")
        self.modbus_conf = None
        if mode == "modbus":
            self.modbus_conf = modbus_conf
            print(self.modbus_conf)
            self.groups = dict()
            self._load_groups()

    def _load_groups(self):
        print("modbus load groups")
        groups_conf = self.modbus_conf.get("groups", [])
        idx = 0
        print(groups_conf)
        for group in groups_conf:
            print(group)
            self.groups[idx] = [int(x, 16) for x in group['slave_address']]
            idx += 1

    def exec_modbus_cmd(self, data, uart_port):
        print("exec modbus cmd")
        if "groups" in data:
            groups_num = data['groups'].get("num")
            cmd = data['groups'].get("cmd")
            try:
                int_cmd = [int(x, 16) for x in cmd]
            except Exception as e:
                print("modbus command error: %s" % e)
                return {"status": 0, "error": e}
            groups_addr = self.groups.get(int(groups_num))
            for addr in groups_addr:
                modbus_cmd = [addr]
                modbus_cmd.extend(int_cmd)
                crc_cmd = modbus_crc(bytearray(modbus_cmd))
                print("modbus uart write")
                print(crc_cmd)
                uart_port.write(crc_cmd)
                utime.sleep(1)
            return {'code': cmd, 'status': 1}
        elif "command" in data:
            command = data['command']
            try:
                int_cmd = [int(x, 16) for x in command]
                crc_cmd = modbus_crc(bytearray(int_cmd))
            except Exception as e:
                print("modbus command error: %s" % e)
                return {"status": 0, "error": e}
            print("modbus write cmd")
            print(crc_cmd)
            uart_port.write(crc_cmd)
            return {'code': command, 'status': 1}
        else:
            err_msg = "can't get any modbus params"
            print(err_msg)
            return {'code': 0, "status": 0, "error": err_msg}

@Singleton
class ChannelTransfer(object):
    def __init__(self):
        self.dtu_c = DTUDocumentData()
        self.channel_dict = CHANNELS
        self.serial_channel_dict = dict()
        # self.control_code = None


@Singleton
class DtuExecCommand(object):

    def __init__(self):
        self.not_need_password_verify_code = [0x00, 0x01, 0x02, 0x03, 0x05]
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
        self.dtu_d = DTUDocumentData()
        #self.ctf = ChannelTransfer()
        #self.offline_storage = OfflineStorage()
        self.search_cmd = DTUSearchCommand()
        self.setting_cmd = BasicSettingCommand()

    def exec_command_code(self, cmd_code, data=None, password=None):
        if data is None:
            data = dict()
        if cmd_code not in self.not_need_password_verify_code:
            # pwd = data.get("password")
            print("pwd")
            print(type(password))
            print(password)
            print("psw")
            print(type(self.dtu_d.password))
            print(self.dtu_d.password)
            if password != self.dtu_d.password:
                logger.error(error_map.get(RET.PASSWDVERIFYERR))
                return {'code': cmd_code, 'status': 0, 'error': error_map.get(RET.PASSWDVERIFYERR)}
        print("EXEC CMD")
        print(cmd_code)
        print(self.search_command_func_code_list)
        print(self.basic_setting_command_list)
        if cmd_code in self.search_command_func_code_list:
            cmd_str = self.search_command.get(cmd_code)
            func = getattr(self.search_cmd, cmd_str)
            rec = func(cmd_code, data)
        elif cmd_code in self.basic_setting_command_list:
            cmd_str = self.basic_setting_command.get(cmd_code)
            func = getattr(self.setting_cmd, cmd_str)
            rec = func(cmd_code, data)
        else:
            # err
            logger.error(error_map.get(RET.POINTERR))
            return {'code': cmd_code, 'status': 0, 'error': error_map.get(RET.POINTERR)}
        return rec
