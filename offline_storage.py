try:
    import uos as os
    import utime as time
    import ujson as json
except:
    import os
    import time
    import json

#os.chdir('/usr/')
from usr.modules.common import Singleton


@Singleton
class OfflineStorage:

    def __init__(self):
        self.status = None
        self.split_file = False
        self.single_file_max = 100
        self._file_name_no = 1
        self._rec_count = 1
        self.default_dir = "/usr/offline_storage_files"
        # self.default_dir = "./"
        self._check_dir()
        self.channels = []
        self._channel_default = "of_default"

    def _check_dir(self):
        try:
            os.chdir(self.default_dir)
        except:
            os.mkdir(self.default_dir)
            # raise SystemError("Directory is not exist!")

    @staticmethod
    def _msg_no_gen():
        ts = int(time.time())
        ts_str = str(ts)
        if len(ts_str) > 5:
            ts = int(ts_str[-5:])
        # 避免时间戳生成时间太短导致重复
        time.sleep(1)
        return ts

    def _get_file_list(self):
        file_list = os.listdir(self.default_dir)
        file_list.sort()
        # 筛选后缀名
        file_filtered = []
        for file in file_list:
            try:
                if file[-5:] == ".json":
                    file_filtered.append(file)
            except:
                continue
        return file_filtered

    def _pre_load(self):
        # 预读取
        data_map = dict()
        file_list = self._get_file_list()
        if not file_list:
            return data_map
        file = file_list.pop()
        with open(self.default_dir + file, 'r', encoding="utf-8") as f:
            try:
                file_map = json.load(f)
            except:
                file_map = dict()
            self._rec_count = len(file_map.keys())
            data_map.update(file_map)
        return data_map

    def _write_file(self, data, channel=None):
        file_list = self._get_file_list()
        file_list.sort()
        if not file_list:
            if self.split_file:
                if self._rec_count > self.single_file_max:
                    self._file_name_no += 1
                file_name = "data%d.json" % self._file_name_no
            else:
                file_name = "data.json"
        else:
            file_name = file_list.pop()
        with open(self.default_dir + file_name, "w+", encoding="utf-8") as f:
            json.dump(data, f)
        self._rec_count += 1

    def deposit(self, data, channel=None):
        if self.status == 'r':
            return False
        self.status = 'w'
        # 序号生成
        if channel is None:
            channel = self._channel_default
        index = self._msg_no_gen()
        format_data = {index: data}
        data_map = self._pre_load()
        channel_map = data_map.get(channel, {})
        channel_map.update(format_data)
        data_map[channel] = channel_map
        self._write_file(data_map)
        self.status = None
        return index

    def take_out(self, channel=None):
        if self.status == 'w':
            return False
        self.status = 'r'
        file_list = self._get_file_list()
        if not file_list:
            return False
        file_list.sort()
        data_map = dict()
        for file in file_list:
            with open(self.default_dir + file, 'r', encoding="utf-8") as f:
                try:
                    data_map.update(json.load(f))
                except:
                    pass
            os.remove(self.default_dir + file)
        if channel is None:
            channel = self._channel_default
        channel_map = data_map.get(channel, {})
        self.status = None
        return channel_map

    def take_out_iter(self, channel=None):
        data_map = self.take_out(channel)
        for k, v in data_map.items():
            yield k, v

    def take_out_list(self, channel=None):
        data_map = self.take_out(channel)
        return list(data_map.values())

    def take_out_by_index(self, index, channel=None):
        if self.status == 'w':
            return False
        self.status = 'r'
        file_list = self._get_file_list()
        if not file_list:
            return None
        file_list.sort()
        if channel is None:
            channel = self._channel_default
        for file in file_list:
            with open(self.default_dir + file, 'r+', encoding="utf-8") as f:
                file_map = json.load(f)
                channel_map = file_map.get(channel, {})
                if index in channel_map:
                    data = channel_map.pop(index)
                    json.dump(file_map, f)
                    return data
        return None

    def take_out_last(self, count=1, channel=None):
        if self.status == 'w':
            return False
        self.status = 'r'
        file_list = self._get_file_list()
        if not file_list:
            return None
        file_list.sort(reverse=True)
        take_out_count = 0
        data_map = dict()
        if channel is None:
            channel = self._channel_default
        for file in file_list:
            with open(self.default_dir + file, 'r+', encoding="utf-8") as f:
                file_map = json.load(f)
                channel_map = file_map.get(channel, {})
                items = sorted(channel_map.items())
                while take_out_count <= count and items:
                    key, values = items.pop()
                    data_map[key] = values
                json.dump(file_map, f)
            if not items:
                os.remove(self.default_dir + file)
        return data_map

    def count(self):
        file_list = self._get_file_list()
        data_count = 0
        for file in file_list:
            with open(self.default_dir + file, 'r', encoding="utf-8") as f:
                try:
                    data_count += len(json.load(f))
                except:
                    pass
        return data_count

    def preview_data(self):
        data_map = dict()
        file_list = self._get_file_list()
        if not file_list:
            return data_map
        file_list.sort()
        for file in file_list:
            with open(self.default_dir + file, 'r', encoding="utf-8") as f:
                try:
                    data_map.update(json.load(f))
                except:
                    pass
        return data_map

    def channel_has_msg(self, channel):
        data_map = self._pre_load()
        msg = data_map.get(channel)
        if msg:
            return True
        else:
            return False

