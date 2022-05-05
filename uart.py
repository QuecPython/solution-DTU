import ubinascii
import utime
import ujson
import log
from machine import Pin
from machine import UART
from usr.modules.common import Singleton
from usr.dtu_channels import ChannelTransfer
from usr.command import DtuExecCommand
from usr.modbus import ModbusMode
from usr.modbus import ThroughMode
from usr.modules.remote import RemotePublish
from usr.modules.logging import getLogger

SERIAL_MAP = dict()
log = getLogger(__name__)

class DtuUart(Singleton):

    def __init__(self, config_params):
        # 配置uart
        uconf = ujson.loads(config_params)["uconf"]
        self.serial_map = SERIAL_MAP
        for sid, conf in uconf.items():
            uart_conn = UART(getattr(UART, 'UART%d' % int(sid)),
                             int(conf.get("baudrate")),
                             int(conf.get("databits")),
                             int(conf.get("parity")),
                             int(conf.get('stopbits')),
                             int(conf.get("flowctl")))
            self.serial_map[sid] = uart_conn
        # 初始化方向gpio
        self._direction_pin(ujson.loads(config_params)["direction_pin"])
        self.cloud_conf = ujson.loads(config_params)["conf"]
        self.work_mode = ujson.loads(config_params)["work_mode"]
        self.exec_cmd = None
        self.exec_modbus = None
        self.cloud_data_parse = None
        self.uart_data_parse = None
        self.concat_buffer = ""
        self.wait_length = 0
        self.wait_retry_count = 0
        self.sub_topic_id = None
        self.cloud_protocol = None
        self.__remote_pub = None
        self.through_mode = None
        self.__channel = None
        if self.work_mode == "command":
            self.exec_cmd = DtuExecCommand()
            self.cloud_data_parse = self.exec_cmd.cloud_data_parse
            self.uart_data_parse = self.exec_cmd.uart_data_parse
        elif self.work_mode == "modbus":
            self.exec_modbus = ModbusMode(self.work_mode, ujson.loads(config_params)["modbus"])
            self.cloud_data_parse = self.exec_modbus.cloud_data_parse
            self.uart_data_parse = self.exec_modbus.uart_data_parse
        else:
            self.through_mode = ThroughMode()
            self.cloud_data_parse = self.through_mode.cloud_data_parse
            self.uart_data_parse = self.through_mode.uart_data_parse

    def set_channel(self, channel):
        print("set channel")
        self.__channel = channel
        if isinstance(self.exec_cmd, DtuExecCommand):
            self.exec_cmd.search_cmd.set_channel(channel)

    def set_procotol_data(self, procotol):
        if self.exec_cmd is not None:
            self.exec_cmd.__protocol = procotol
        elif self.exec_modbus is not None:
            self.exec_modbus.__protocol = procotol
        elif self.through_mode is not None:
            self.through_mode.__protocol = procotol

    def add_module(self, module, callback=None):
        if isinstance(module, RemotePublish):
            self.__remote_pub = module
            return True

    def remote_post_data(self, channel_id, topic_id=None, data=None):
        if not self.__remote_pub:
            raise TypeError("self.__remote_pub is not registered.")
        print("test51")
        return self.__remote_pub.post_data(data, channel_id, topic_id)

    def cloud_parse_proc(self, cloud, *args, **kwargs):
        topic_id = None
        channel_id = None
        serial_id = None

        if kwargs["topic"] is not None:
            for k, v in cloud.sub_topic_dict.items():
                if kwargs["topic"] == v:
                    topic_id = k
        
        for k, v in self.__channel.cloud_object_dict.items():
            if cloud == v:
                channel_id = k
        
        for sid, cid in self.__channel.serial_channel_dict.items():
            if channel_id in cid:
                serial_id = sid

        ret_data = self.cloud_data_parse(kwargs["data"], topic_id, channel_id)

        # reply cloud query command
        if ret_data["cloud_data"] is not None:
            self.remote_post_data(self, channel_id, topic_id, ret_data["cloud_data"])
        #send to uart cloud message
        if ret_data["uart_data"] is not None:
            uart_port = self.serial_map.get(str(serial_id))
            uart_port.write(ret_data["uart_data"])
  
    def gui_tools_parse(self, gui_data, sid):
        print(gui_data)
        gui_data = gui_data.decode()
        data_list = gui_data.split(",", 3)
        print(data_list)
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
            self.concat_buffer = ""
            self.wait_length = 0
            return False
        # 更改数据不完整,存入buffer,尝试继续读取
        elif len(msg_data) < data_len_int:
            log.info("Msg length shorter than length")
            self.concat_buffer = gui_data
            self.wait_length = data_len_int - int(msg_data)
            return True
        data_crc = self.protocol.crc32(msg_data)
        if crc32_val != data_crc:
            log.error("DTU CMD CRC32 vaildate failed")
            return False
        try:
            data = ujson.loads(msg_data)
        except Exception as e:
            log.error(e)
            return False
        cmd_code = data.get("cmd_code")
        # 未获得命令码
        if cmd_code is None:
            return False
        params_data = data.get("data")
        password = data.get("password", None)
        rec = self.exec_cmd.exec_command_code(int(cmd_code), data=params_data, password=password)
        rec_str = ujson.dumps(rec)
        print(rec_str)
        print(len(rec_str))
        rec_crc_val = self.protocol.crc32(rec_str)
        rec_format = "{},{},{}".format(len(rec_str), rec_crc_val, rec_str)
        # 获取需要返回数据的serialID
        uart = self.serial_map.get(str(sid))
        print(uart)
        uart.write(rec_format.encode('utf-8'))
        print(rec_format)
        print('GUI CMD SUCCESS')
        return True

    # to online
    def uart_read_handler(self, data, sid):
        print("sid:", sid)
        print("__channel.serial_channel_dict:", self.__channel.serial_channel_dict)
        serial_channels = self.__channel.serial_channel_dict.get(int(sid))
        if not serial_channels:
            log.error("Serial Config not exist!")
            return False
        # 移动gui判断逻辑
        gui_flag = self.gui_tools_parse(data, sid)
        if gui_flag:
            return False
        print("test41")
        read_msg, send_params = self.uart_data_parse(data, self.__channel.cloud_channel_dict, serial_channels)
        print("read_msg:", read_msg)
        print("send_params:", send_params)
        print("test46")
        if read_msg is False:
            return False
        
        if len(send_params) == 2:
            self.remote_post_data(channel_id=send_params[0], topic_id=send_params[1], data=read_msg)
        elif len(send_params) == 1:
            self.remote_post_data(channel_id=send_params[0], data=read_msg)

    def read(self):
        while 1:
            # 返回是否有可读取的数据长度
            for sid, uart in self.serial_map.items():
                msgLen = uart.any()
                # 当有数据时进行读取
                if msgLen:
                    msg = uart.read(msgLen)
                    print(msg)
                    try:
                        # 初始数据是字节类型（bytes）,将字节类型数据进行编码
                        self.uart_read_handler(msg, sid)
                    except Exception as e:
                        log.error("UART handler error: %s" % e)
                        utime.sleep_ms(100)
                        continue
                else:
                    utime.sleep_ms(100)
                    continue

    def _direction_pin(self, direction_pin=None):
        if direction_pin == None:
            return
        print(direction_pin)
        for sid, conf in direction_pin.items():
            uart = self.serial_map.get(str(sid))
            gpio = getattr(Pin, "GPIO%s" % str(conf.get("GPIOn")))
            # 输出电平
            direction_level = conf.get("direction")
            uart.control_485(gpio, direction_level)
