import ubinascii
import utime
import ujson
import log
from machine import Pin
from machine import UART
from usr.singleton import Singleton
from usr.settings import DTUDocumentData
from usr.command import ChannelTransfer
from usr.command import DtuExecCommand
from usr.command import ModbusCommand
from usr.dtu_log import RET
from usr.dtu_log import error_map


SERIAL_MAP = dict()
log.basicConfig(level=log.INFO)
logger = log.getLogger(__name__)


@Singleton
class DtuProtocolData(object):

    def __init__(self):
        self.crc_table = []
        self._create_table()

    def _create_table(self):
        poly = 0xEDB88320
        a = []
        for byte in range(256):
            crc = 0
            for bit in range(8):
                if (byte ^ crc) & 1:
                    crc = (crc >> 1) ^ poly
                else:
                    crc >>= 1
                byte >>= 1
            a.append(crc)
        self.crc_table = a

    def crc32(self, crc_string):
        value = 0xffffffff
        for ch in crc_string:
            value = self.crc_table[(ord(ch) ^ value) & 0xff] ^ (value >> 8)
        crc_value = str((-1 - value) & 0xffffffff)
        return crc_value

    def data_package(self, data, http=False):
        data_len = len(data)
        crc_value = self.crc32(data)
        if not http or (http and data_len != 0):
            return {'msg_len': data_len, "crc_32": crc_value, "data": data}
        else:
            return {'msg_len': data_len}

    def validate_data(self, data, http=False):
        msg_len = data.get("data_len", None)
        if msg_len is None:
            return False
        crc_32 = data.get("crc_32", None)
        msg_data = data.get("data", None)
        if http and msg_len == 0 and crc_32 is None and msg_data is None:
            return True
        if not isinstance(msg_data, str):
            msg_data = ujson.dumps(msg_data)
        cal_crc32 = self.crc32(msg_data)
        if cal_crc32 == crc_32:
            return True
        else:
            return False

@Singleton
class DtuUart(object):

    def __init__(self, config_params):
        self.dtu_d = DTUDocumentData()
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
        self.channels = ChannelTransfer()
        self.exec_cmd = DtuExecCommand()
        self.exec_modbus = ModbusCommand(ujson.loads(config_params)["work_mode"], ujson.loads(config_params)["modbus"])
        self.protocol = DtuProtocolData()
        self.concat_buffer = ""
        self.wait_length = 0
        self.wait_retry_count = 0
        self.sub_topic_id = None
        self.cloud_protocol = None

    def parity_flag(self, data):
        global parity
        if data == "NONE":
            parity = 0
        if data == "EVENT":
            parity = 1
        if data == "ODD":
            parity = 2
        return parity

    # 云端to设备,命令
    def output(self, data, serial_id, mqtt_id=None, request_id=None, pkgid=None):
        if mqtt_id is None and request_id is None:
            return False
        print("OUTPUT DATAS")
        print(type(data))
        print(data)

        if isinstance(data, (int, float)):
            data = str(data)
        # 获取从云端接收到的topic 的id，通过串口下行到外接设备 
        if mqtt_id is not None:
            self.sub_topic_id = 0
            for cid, channel in self.cloud_conf.items():
                print("channel:", channel)
                for k, sub_topic in channel.get("subscribe").items():
                    print("sub_topic:", sub_topic)
                    print("mqtt_id:", mqtt_id)
                    if sub_topic == mqtt_id.decode():
                        self.sub_topic_id = k
                        self.cloud_protocol = channel.get("protocol")


        if self.cloud_protocol == "hwyun":
            data = ujson.loads(data)
            data = data["content"]
        print("data:", data)
        if self.dtu_d.work_mode in ['command', "modbus"]:
            print("CMD START")
            try:
                if isinstance(data, str):
                    msg_data = ujson.loads(data)
                elif isinstance(data, bytes):
                    msg_data = ujson.loads(str(data))
                elif isinstance(data, dict):
                    msg_data = data
                else:
                    raise error_map.get(RET.CMDPARSEERR)
                cmd_code = msg_data.get("cmd_code", None)
                modbus_data = msg_data.get("modbus", None)
                msg_id = msg_data.get("msg_id")
                password = msg_data.get("password", None)
                cloud_request_topic = msg_data.get("topic_id", None)
                if cmd_code is not None:
                    rec = self.exec_cmd.exec_command_code(cmd_code, data=msg_data, password=password)
                    rec['msg_id'] = msg_id
                    if cloud_request_topic is not None:
                        rec['topic_id'] = cloud_request_topic

                    print("CMD END")
                    print(rec)
                    return rec
                elif modbus_data is not None:
                    uart_port = self.serial_map.get(str(serial_id))
                    if uart_port is None:
                        print("UART serial id error")
                        return False
                    rec = self.exec_modbus.exec_modbus_cmd(modbus_data, uart_port)
                    return rec
            except Exception as e:
                logger.info("{}: {}".format(error_map.get(RET.CMDPARSEERR), e))
        # package_data
        uart_port = self.serial_map.get(str(serial_id))
        if uart_port is None:
            logger.error("UART serial id error")
            return False
        topic_id = self.sub_topic_id if self.sub_topic_id != None else pkgid
        # 命令模式下发送数据需要注明通道id
        if self.dtu_d.work_mode == "command":
            package_data = self.package_datas(data, topic_id, request_id)
        elif self.dtu_d.work_mode == "through":
            package_data = self.package_datas(data, topic_id)
        print("package_data:", package_data)
        uart_port.write(package_data)
        return True

    def package_datas(self, msg_data, topic_id=False, request_msg=False):
        print(msg_data)
        if len(msg_data) == 0:
            if request_msg is not False:
                ret_bytes = "%s,%s,%d".encode('utf-8') % (str(request_msg), str(topic_id), len(msg_data))
            else:
                ret_bytes = "%s,%d".encode('utf-8') % (str(topic_id), len(msg_data))
        else:
            crc32_val = self.protocol.crc32(str(msg_data))
            msg_length = len(str(msg_data))
            if request_msg is not False:
                ret_bytes = "%s,%s,%s,%s,%s".encode('utf-8') % (str(request_msg), str(topic_id), str(msg_length), str(crc32_val), str(msg_data))
            else:
                ret_bytes = "%s,%s,%s,%s".encode('utf-8') % (str(topic_id), str(msg_length), str(crc32_val), str(msg_data))
        return ret_bytes

    def validate_length(self, data_len, msg_data, str_msg):
        if len(msg_data) < data_len:
            self.concat_buffer = str_msg
            self.wait_length = data_len - len(msg_data)
            print("wait length")
            print(self.wait_length)
            return False
        elif len(msg_data) > data_len:
            self.concat_buffer = ""
            self.wait_length = 0
            return False
        else:
            self.concat_buffer = ""
            self.wait_length = 0
            return True

    # 设备to云端
    def unpackage_datas(self, str_msg, channels, sid):
        # 移动gui判断逻辑
        gui_flag = self.gui_tools_parse(str_msg, sid)
        # gui命令主动终止
        if gui_flag:
            return False, []
        # 避免后续pop操作影响已有数据
        channels_copy = [x for x in channels]
        print("dtu word mode")
        print(self.dtu_d.work_mode)
        try:
            if self.dtu_d.work_mode == 'command':
                params_list = str_msg.split(",", 4)
                if len(params_list) not in [2, 4, 5]:
                    logger.error("param length error")
                    return False, []
                channel_id = params_list[0]
                channel = self.channels.channel_dict.get(str(channel_id))
                if not channel:
                    logger.error("Channel id not exist. Check serialID config.")
                    return False, []
                if channel.conn_type in ['http', 'tcp', 'udp']:
                    msg_len = params_list[1]
                    if msg_len == "0":
                        return {}, [channel]
                    else:
                        crc32 = params_list[2]
                        msg_data = params_list[3]
                        try:
                            msg_len_int = int(msg_len)
                        except:
                            logger.error("data parse error")
                            return False, []
                        valid_rec = self.validate_length(msg_len_int, msg_data, str_msg)
                        if not valid_rec:
                            return False, []
                        cal_crc32 = self.protocol.crc32(msg_data)
                        if cal_crc32 == crc32:
                            return {"data": msg_data}, [channel]
                        else:
                            logger.error("crc32 error")
                            return False, []
                else:
                    topic_id = params_list[1]
                    msg_len = params_list[2]
                    crc32 = params_list[3]
                    msg_data = params_list[4]
                    try:
                        msg_len_int = int(msg_len)
                    except:
                        logger.error("data parse error")
                        return False, []
                    # 加入buffer
                    valid_rec = self.validate_length(msg_len_int, msg_data, str_msg)
                    if not valid_rec:
                        return False, []
                    cal_crc32 = self.protocol.crc32(msg_data)
                    if crc32 == cal_crc32:
                        return {'data': msg_data}, [channel, topic_id]
                    else:
                        return False, []
            elif self.dtu_d.work_mode == 'modbus':
                channel_id = channels_copy.pop()
                channel = self.channels.channel_dict.get(str(channel_id))
                if not channel:
                    print("Channel id not exist. Check serialID config.")
                    return False, []
                print("modbus str_msg")
                print(type(str_msg))
                print(str_msg)
                modbus_data_list = str_msg.split(",")
                hex_list = ["0x" + x for x in modbus_data_list]
                # 返回channel
                if channel.conn_type in ['http', 'tcp', 'udp',]:
                    return hex_list, [channel]
                else:
                    topics = list(channel.pub_topic.keys())
                    return hex_list, [channel, topics[0]]
            # 透传模式
            else:
                params_list = str_msg.split(",", 3)
                if len(params_list) not in [1, 3, 4]:
                    return False, [None]
                channel_id = channels_copy.pop()
                channel = self.channels.channel_dict.get(str(channel_id))
                if not channel:
                    logger.error("Channel id not exist. Check serialID config.")
                    return False, []
                if channel.conn_type in ['http', 'tcp', 'udp']:
                    msg_len = params_list[0]
                    if msg_len == "0":
                        return "", [channel]
                    else:
                        crc32 = params_list[1]
                        msg_data = params_list[2]
                        try:
                            msg_len_int = int(msg_len)
                        except:
                            logger.error("data parse error")
                            return False, []
                        #  加入buffer
                        valid_rec = self.validate_length(msg_len_int, msg_data, str_msg)
                        if not valid_rec:
                            return False, []
                        cal_crc32 = self.protocol.crc32(msg_data)
                        if crc32 == cal_crc32:
                            return msg_data, [channel]
                        else:
                            logger.error("crc32 error")
                            return False, []
                else:
                    topic_id = params_list[0]
                    msg_len = params_list[1]
                    crc32 = params_list[2]
                    msg_data = params_list[3]
                    try:
                        msg_len_int = int(msg_len)
                    except:
                        logger.error("data parse error")
                        return False, []
                    # 加入buffer
                    valid_rec = self.validate_length(msg_len_int, msg_data, str_msg)
                    if not valid_rec:
                        return False, []
                    cal_crc32 = self.protocol.crc32(msg_data)
                    if crc32 == cal_crc32:
                        return msg_data, [channel, topic_id]
                    else:
                        logger.error("crc32 error")
                        return False, []
        except Exception as e:
            # 数据解析失败,丢弃
            logger.error("{}: {}".format(error_map.get(RET.DATAPARSEERR), e))
            # 强制清空buffer
            self.concat_buffer = ""
            self.wait_length = 0
            return False, []

    def gui_tools_parse(self, gui_data, sid):
        print(gui_data)
        data_list = gui_data.split(",", 3)
        print(data_list)
        if len(data_list) != 4:
            logger.info("DTU CMD list length validate fail. CMD Parse end.")
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
            logger.error("DTU CMD data error.")
            return False
        if len(msg_data) > data_len_int:
            logger.error("DTU CMD length validate failed.")
            self.concat_buffer = ""
            self.wait_length = 0
            return False
        # 更改数据不完整,存入buffer,尝试继续读取
        elif len(msg_data) < data_len_int:
            logger.info("Msg length shorter than length")
            self.concat_buffer = gui_data
            self.wait_length = data_len_int - int(msg_data)
            return True
        data_crc = self.protocol.crc32(msg_data)
        if crc32_val != data_crc:
            logger.error("DTU CMD CRC32 vaildate failed")
            return False
        try:
            data = ujson.loads(msg_data)
        except Exception as e:
            logger.error(e)
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
        channels = self.channels.serial_channel_dict.get(int(sid))
        if not channels:
            logger.error("Serial Config not exist!")
            return False
        try:
            if self.dtu_d.work_mode == "modbus":
                str_msg = ubinascii.hexlify(data, ',').decode()
            else:
                str_msg = data.decode()
        except:
            return False
        read_msg, send_params = self.unpackage_datas(str_msg, channels, sid)
        if read_msg is False:
            return False
        if len(send_params) == 2:
            channel = send_params[0]
            topic = send_params[1]
            # 移远云发送不需要指定topic
            if channel.conn_type == "quecthing":
                channel.send(read_msg)
            else:
                channel.send(read_msg, topic)
        elif len(send_params) == 1:
            channel = send_params[0]
            channel.send(read_msg)

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
                        logger.error("UART handler error: %s" % e)
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
