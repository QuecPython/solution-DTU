from usr.modules.common import Singleton

class ChannelTransfer(Singleton):
    def __init__(self, woke_mode, channels_conf):
        # channel_dict字典中key值是云通道序号（”1“），v值是不同的云配置
        self.cloud_channel_dict = dict()

        # cloud_object_dict字典中key值是云通道序号（”1“），v值是不同的云对象
        self.cloud_object_dict = dict()

        # serial_channel_dict字典中每个串口号对应一个数组，数组中记录着串口号对应的云通道序号，在command模式下每个串口号可能对应多个云通道，其他模式都是一对一
        self.serial_channel_dict = dict()

        self.init(self, woke_mode, channels_conf)
    
    def init(self, woke_mode, channels_conf):
        # serial_channel_dict字典中每个串口号对应一个数组，数组中记录着串口号对应的云通道序号
        # 在command模式下每个串口号可能对应多个云通道，其他模式都是一对一
        if woke_mode == 'command':
            for cid, channel in channels_conf.items():
                serial_id = int(channel.get("serialID"))
                if serial_id in self.channel.serial_channel_dict:
                    self.channel.serial_channel_dict[serial_id].append(cid)
                else:
                    self.channel.serial_channel_dict[serial_id] = [cid]
            self.channel_dict = channels_conf
        else:
            serv_map = dict()
            serial_list = [0, 1, 2]
            for cid, channel in channels_conf.items():
                serial_id = int(channel.get("serialID"))
                if serial_id in serial_list:
                    serv_map[cid] = channel
                    self.channel.serial_channel_dict[serial_id] = [cid]
                    serial_list.remove(serial_id)
                else:
                    continue
            self.channel_dict = serv_map