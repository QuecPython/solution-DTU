from usr.modules.common import Singleton
from usr.modules.logging import error_map
from usr.modules.logging import RET
from usr.modules.logging import getLogger

log = getLogger(__name__)

class ThroughMode(Singleton):
    def __init__(self):
        self.__protocol = None

    def set_protocol(self, protocol):
        self.__protocol = protocol

    def cloud_data_parse(self, data, topic_id, channel_id):
        ret_data = {"cloud_data":None, "uart_data":None}

        if isinstance(data, (int, float)):
            data = str(data)
        package_data = self.__protocol.package_datas(data, topic_id)
        print("package_data:", package_data)
        ret_data["uart_data"] = package_data
        return ret_data

    def uart_data_parse(self, data, cloud_channel_dict, cloud_channel_array=None):
        str_msg = data.decode()
        params_list = str_msg.split(",")
        if len(params_list) not in [2, 4, 5]:
            log.error("param length error")
            return False, []
        # Modbus模式和透传模式 下一个串口通道只能绑定一个云端口
        cloud_channel_id = cloud_channel_array[0]
        channel = cloud_channel_dict.get(str(cloud_channel_id))
        if not channel:
            log.error("Channel id not exist. Check serialID config.")
            return False, []
        print("channel.get(protocol):", channel.get("protocol"))
        if channel.get("protocol") in ["http", "tcp", "udp"]:
            msg_len = params_list[1]
            if msg_len == "0":
                return "", [cloud_channel_id]
            else:
                crc32 = params_list[1]
                msg_data = params_list[2]
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
                    return msg_data, [cloud_channel_id]
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
            valid_rec = self.__protocol.validate_length(msg_len_int, msg_data, str_msg)
            if not valid_rec:
                return False, []
            cal_crc32 = self.__protocol.crc32(msg_data)
            if crc32 == cal_crc32:
                return msg_data, [cloud_channel_id, topic_id]
            else:
                return False, []