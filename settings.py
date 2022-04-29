import ujson
import uos
import modem
from usr.modules.common import Singleton
from usr.modules.logging import RET
from usr.modules.logging import error_map
from usr.modules.logging import getLogger

log = getLogger(__name__)

PROJECT_NAME = "QuecPython-Tracker"

PROJECT_VERSION = "2.1.0"

DEVICE_FIRMWARE_NAME = uos.uname()[0].split("=")[1]

DEVICE_FIRMWARE_VERSION = modem.getDevFwVersion()

CONFIG = {
    "config_dir": "/usr",
    "config_path": "/usr/dtu_config.json",
    "backup_path": "/usr/dtu_config.json.bak",
    "config_default_path": "/usr/dtu_default_config.json"
}

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
                    with open(CONFIG['config_backup_path'], mode="r") as f:
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
