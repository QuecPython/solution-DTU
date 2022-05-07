from usr.modules.common import Singleton

class DtuProtocolData(Singleton):

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

    def package_datas(self, msg_data, topic_id=None, channel_id=None):
        print(msg_data)

        msg_length = len(str(msg_data))
        topic_id_str = str(topic_id) if topic_id is not None else ""
        channel_id_str = str(channel_id) if channel_id is not None else ""

        if len(msg_data) == 0:
            ret_bytes = "%s,%s,%d".encode("utf-8") % (channel_id_str, topic_id_str, msg_length)
        else:
            crc32_val = self.crc32(str(msg_data))
            ret_bytes = "%s,%s,%d,%d,%s".encode("utf-8") % (channel_id_str, topic_id_str, msg_length, crc32_val, str(msg_data))
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

