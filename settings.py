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

import ure
import uos
import ql_fs
import ujson
import modem
import _thread

from usr.modules.common import Singleton
from usr.modules.common import option_lock
from usr.modules.logging import RET
from usr.modules.logging import error_map
from usr.modules.logging import getLogger

log = getLogger(__name__)

PROJECT_NAME = "QuecPython-Dtu"
PROJECT_VERSION = "2.1.0"

DEVICE_FIRMWARE_NAME = uos.uname()[0].split("=")[1]
DEVICE_FIRMWARE_VERSION = modem.getDevFwVersion()

_settings_lock = _thread.allocate_lock()

CONFIG = {
    "config_dir": "/usr",
    "config_path": "/usr/dtu_config.json",
}


class Settings(Singleton):

    def __init__(self, settings_file=CONFIG["config_path"]):
        self.settings_file = settings_file
        self.current_settings = {}
        self.init()

    def __init_config(self):
        try:
            """
            self.current_settings["sys"] = {k: v for k, v in SYSConfig.__dict__.items() if not k.startswith("_")}

            # CloudConfig init
            if self.current_settings["sys"]["cloud"] == SYSConfig._cloud.AliYun:
                self.current_settings["cloud"] = {k: v for k, v in AliCloudConfig.__dict__.items() if not k.startswith("_")}
            elif self.current_settings["sys"]["cloud"] == SYSConfig._cloud.quecIot:
                self.current_settings["cloud"] = {k: v for k, v in QuecCloudConfig.__dict__.items() if not k.startswith("_")}
            elif self.current_settings["sys"]["cloud"] == SYSConfig._cloud.JTT808:
                self.current_settings["cloud"] = {k: v for k, v in JTT808Config.__dict__.items() if not k.startswith("_")}
            elif self.current_settings["sys"]["cloud"] == SYSConfig._cloud.customization:
                self.current_settings["cloud"] = {}
            else:
                self.current_settings["cloud"] = {}

            # LocConfig init
            if self.current_settings["sys"]["base_cfg"]["LocConfig"]:
                self.current_settings["LocConfig"] = {k: v for k, v in LocConfig.__dict__.items() if not k.startswith("_")}

            # UserConfig init
            if self.current_settings["sys"]["user_cfg"]:
                self.current_settings["user_cfg"] = {k: v for k, v in UserConfig.__dict__.items() if not k.startswith("_")}
                self.current_settings["user_cfg"]["ota_status"]["sys_current_version"] = DEVICE_FIRMWARE_VERSION
                self.current_settings["user_cfg"]["ota_status"]["app_current_version"] = PROJECT_VERSION
            """
            return True
        except:
            return False

    def __read_config(self):
        if ql_fs.path_exists(self.settings_file):
            with open(self.settings_file, "r") as f:
                self.current_settings = ujson.load(f)
                return True
        return False

    def __set_config(self, opt, val):
        if opt == "ota_status":
                if not isinstance(val, dict):
                    return False
                self.current_settings["user_cfg"][opt] = val
                return True
        elif opt == "cloud":
            if not isinstance(val, dict):
                return False
            self.current_settings[opt] = val
            return True

        return False

    def __save_config(self):
        try:
            with open(self.settings_file, "w") as f:
                ujson.dump(self.current_settings, f)
            return True
        except:
            return False

    def __remove_config(self):
        try:
            uos.remove(self.settings_file)
            return True
        except:
            return False

    def __get_config(self):
        return self.current_settings
        
    @option_lock(_settings_lock)
    def init(self):
        if self.__read_config() is False:
            if self.__init_config():
                return self.__save_config()
        return False

    @option_lock(_settings_lock)
    def get(self):
        return self.__get_config()

    @option_lock(_settings_lock)
    def set(self, opt, val):
        return self.__set_config(opt, val)

    @option_lock(_settings_lock)
    def save(self):
        return self.__save_config()

    @option_lock(_settings_lock)
    def remove(self):
        return self.__remove_config()

    @option_lock(_settings_lock)
    def reset(self):
        if self.__remove_config():
            if self.__init_config():
                return self.__save_config()
        return False

settings = Settings()


class ProdDocumentParse(object):

    def __init__(self):
        self.document = ""

    def read(self, config_path):
        if not self.document:
            self.refresh_document(config_path)

    def refresh_document(self, config_path):
        try:
            with open(config_path, mode="r") as f:
                self.document = f.read()
            return self.document  # new
        except Exception as e:
            # 加载旧版本文件
            try:
                with open(config_path + ".bak", mode="r") as f:
                    self.document = f.read()
                return self.document
            except Exception as e:
                # 加载出厂文件
                try:
                    with open(CONFIG["config_backup_path"], mode="r") as f:
                        self.document = f.read()
                    return self.document
                except:
                    print("'dtu_config.json', last version and default config not exist")
                    raise Exception(RET.READFILEERR)

    def _parse_document(self, parser_obj):
        try:
            document_loader = ujson.loads(self.document)
        except Exception as e:
            print(error_map.get(RET.JSONLOADERR))
            raise RET.JSONLOADERR
        try:
            dtu_data_obj = parser_obj.reload(**document_loader)
        except Exception as e:
            # print("e = {}".format(e))
            print("{}: {}".format(error_map.get(RET.JSONLOADERR), e))
            raise RET.JSONPARSEERR
        return dtu_data_obj

    def parse(self, parser_obj):
        config_path = CONFIG["config_path"]
        if not self.exist_config_file(config_path):
            # 从uart口读取数据
            print(error_map.get(RET.CONFIGNOTEXIST))
        else:
            self.read(config_path=config_path)
            return self._parse_document(parser_obj=parser_obj)

    @staticmethod
    def exist_config_file(config_path):
        config_split = config_path.rsplit("/", 1)
        return config_split[1] in uos.listdir(config_split[0])


class DTUDocumentData(Singleton):

    def __init__(self):
        self.fota = 1
        self.nolog = 1
        self.plate = 1
        self.reg = 1
        self.convert = 0
        self.service_acquire = 1
        self.version = ""
        self.password = ""
        self.message = {}
        self.uconf = dict()
        self.conf = dict()
        self.pins = []
        self.apn = []
        self.modbus = dict()
        self.work_mode = "command"
        self.auto_connect = True
        self.offline_storage = False
        self.ota = []

    def json_info(self, need=True):
        data_info = dict()
        for key in self.__dict__.keys():
            data_info[key] = getattr(self, key)
        if need:
            return ujson.dumps(data_info)
        else:
            return data_info

    def reload_file(self):
        try:
            with open(CONFIG["config_path"], mode="w") as f:
                f.write(self.json_info())
        except Exception as e:
            log.error(e)
            log.info("*****'dtu_config.json' not exist*****")
            return

    def reload(self, **kwargs):
        for key in self.__dict__.keys():
            if key in kwargs:
                setattr(self, key, kwargs[key])
            else:
                setattr(self, key, type(getattr(self, key))())

    def backup_file(self):
        try:
            new_path = CONFIG["config_path"] + ".new"
            with open(new_path, mode="w") as f:
                f.write(self.json_info())
            uos.rename(CONFIG["config_path"], CONFIG["config_path"] + ".old")
            uos.rename(new_path, CONFIG["config_path"])
        except Exception as e:
            log.error(e)
            log.info("*****'dtu_config.json' not exist*****")
            return
