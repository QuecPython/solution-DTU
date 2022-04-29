import ujson
import utime
import ubinascii
from usr.modules.common import Singleton
from usr.dtu_protocol_data import DtuProtocolData
from usr.modules.logging import error_map
from usr.modules.logging import RET
from usr.modules.logging import getLogger

log = getLogger(__name__)

def modbus_crc(string_byte):
    crc = 0xFFFF
    for pos in string_byte:
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
    string_byte.append(high)
    string_byte.append(low)
    return string_byte


class ModbusMode(Singleton):
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

    def cloud_data_parse(self, data):
        ret_data = {"cloud_data":None, "uart_data":None}

        try:
            if isinstance(data, str):
                msg_data = ujson.loads(data)
            elif isinstance(data, bytes):
                msg_data = ujson.loads(str(data))
            elif isinstance(data, dict):
                msg_data = data
            else:
                raise error_map.get(RET.CMDPARSEERR)
            modbus_data = msg_data.get("modbus", None)
            if modbus_data is not None:
                if "groups" in data:
                    groups_num = data['groups'].get("num")
                    cmd = data['groups'].get("cmd")
                    try:
                        int_cmd = [int(x, 16) for x in cmd]
                    except Exception as e:
                        print("modbus command error: %s" % e)
                        ret_data["cloud_data"] = {"status": 0, "error": e}
                    groups_addr = self.groups.get(int(groups_num))
                    for addr in groups_addr:
                        modbus_cmd = [addr]
                        modbus_cmd.extend(int_cmd)
                        crc_cmd = modbus_crc(bytearray(modbus_cmd))
                        print(crc_cmd)
                        ret_data["uart_data"] = crc_cmd
                        utime.sleep(1)
                    ret_data["cloud_data"] = {'code': cmd, 'status': 1}
                elif "command" in data:
                    command = data['command']
                    try:
                        int_cmd = [int(x, 16) for x in command]
                        crc_cmd = modbus_crc(bytearray(int_cmd))
                    except Exception as e:
                        print("modbus command error: %s" % e)
                        ret_data["cloud_data"] = {"status": 0, "error": e}
                    print("modbus write cmd")
                    print(crc_cmd)
                    ret_data["uart_data"] = crc_cmd
                    ret_data["cloud_data"] = {"code": command, "status": 1}
                else:
                    err_msg = "can't get any modbus params"
                    print(err_msg)
                    ret_data["cloud_data"] = {"code": 0, "status": 0, "error": err_msg}
            return ret_data
        except Exception as e:
                log.info("{}: {}".format(error_map.get(RET.CMDPARSEERR), e))

    def uart_data_parse(self, data, channels):
        str_msg = ubinascii.hexlify(data, ',').decode()
        channel_id = channels.pop()
        channel = self.channels.cloud_object_dict.get(str(channel_id))
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
            return hex_list, [channel_id]
        else:
            topics = list(channel.pub_topic.keys())
            return hex_list, [channel_id, topics[0]]
@Singleton
class ThroughMode:
    def __init__(self):
        self.protocol = DtuProtocolData()

    def cloud_data_parse(self, data, topic_id, channel_id):
        ret_data = {"cloud_data":None, "uart_data":None}

        if isinstance(data, (int, float)):
            data = str(data)
        package_data = self.protocol.package_datas(data, topic_id)
        ret_data["uart_data"] = package_data

    def uart_data_parse(self, data, channels=None):
        str_msg = data.decode()
        params_list = str_msg.split(",")
        if len(params_list) not in [2, 4, 5]:
            log.error("param length error")
            return False, []
        channel_id = channels.pop()
        channel = self.channels.cloud_object_dict.get(str(channel_id))
        if not channel:
            log.error("Channel id not exist. Check serialID config.")
            return False, []
        if channel.conn_type in ['http', 'tcp', 'udp']:
            msg_len = params_list[1]
            if msg_len == "0":
                return "", [channel_id]
            else:
                crc32 = params_list[1]
                msg_data = params_list[2]
                try:
                    msg_len_int = int(msg_len)
                except:
                    log.error("data parse error")
                    return False, []
                valid_rec = self.validate_length(msg_len_int, msg_data, str_msg)
                if not valid_rec:
                    return False, []
                cal_crc32 = self.protocol.crc32(msg_data)
                if cal_crc32 == crc32:
                    return msg_data, [channel_id]
                else:
                    log.error("crc32 error")
                    return False, []
        else:
            topic_id = params_list[0]
            msg_len = params_list[1]
            crc32 = params_list[2]
            msg_data = params_list[3]
            try:
                msg_len_int = int(msg_len)
            except:
                log.error("data parse error")
                return False, []
            # 加入buffer
            valid_rec = self.validate_length(msg_len_int, msg_data, str_msg)
            if not valid_rec:
                return False, []
            cal_crc32 = self.protocol.crc32(msg_data)
            if crc32 == cal_crc32:
                return msg_data, [channel_id, topic_id]
            else:
                return False, []