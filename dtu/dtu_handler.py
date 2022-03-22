import log, sim, uos, dataCall, ujson, request, usocket, net, log, modem, utime, _thread, uhashlib, ubinascii, fota, ure, audio, ntptime, urandom, sms
import cellLocator
import quecIot
import hmac
from machine import Pin
from misc import Power, ADC
from aLiYun import aLiYun
from TenCentYun import TXyun
from umqtt import MQTTClient
from machine import UART
uos.chdir('/usr/')
from singleton import Singleton
from t_h import SensorTH
from offline_storage import OfflineStorage

log.basicConfig(level=log.INFO)
logger = log.getLogger("dtu")


# ota 升级优化
# 新增系统日志上报功能
class RET:
    OK = "20000"
    HTTP_OK = "20001"
    MQTT_OK = "20002"
    SOCKET_TCP_OK = "20003"
    SOCKET_UDP_OK = "20004"
    Aliyun_OK = "20005"
    TXyun_OK = "20006"
    # 系统组件错误
    SIMERR = "3001"
    DIALINGERR = "3002"
    # 网络协议错误
    HTTPERR = "4001"
    REQERR = "4002"
    TCPERR = "4003"
    UDPERR = "4004"
    MQTTERR = "4005"
    ALIYUNMQTTERR = "4006"
    TXYUNMQTTERR = "4007"
    PROTOCOLERR = "4008"
    REQERR1 = "4009"
    QUECIOTERR = "4010"
    HWYUNERR = "4011"
    REQERR2 = "5000"
    # 功能错误
    PASSWORDERR = "5001"
    PASSWDVERIFYERR = "5002"
    HTTPCHANNELPARSEERR = "5003"
    CHANNELERR = "5004"
    DATATYPEERR = "5005"
    METHODERR = "5006"
    DATASENDERR = "5007"
    IOTTYPERR = "5008"
    NUMBERERR = "5009"
    MODBUSERR = "5010"
    # 解析错误
    JSONLOADERR = "6001"
    JSONPARSEERR = "6002"
    PARSEERR = "6003"
    DATAPARSEERR = "6004"
    POINTERR = "6005"
    READFILEERR = "6006"
    CONFIGNOTEXIST = "6007"
    # 提醒
    CMDPARSEERR = "7001"


error_map = {
    RET.OK: u"成功",
    RET.HTTP_OK: u"http connect success",
    RET.MQTT_OK: u"mqtt connect success",
    RET.SOCKET_TCP_OK: u"tcp connect success",
    RET.SOCKET_UDP_OK: u"udp connect success",
    RET.Aliyun_OK: u"aliyun connect success",
    RET.TXyun_OK: u"txyun connect success",
    # 系统
    RET.SIMERR: u"read sim card error",
    RET.DIALINGERR: u"dialing error",
    # 协议
    RET.HTTPERR: u"http request error",
    RET.REQERR: u"http request 500",
    RET.REQERR1: u"http request 302",
    RET.REQERR2: u"http request 404",
    RET.TCPERR: u"tcp connect failed",
    RET.UDPERR: u"udp connect failed",
    RET.MQTTERR: u"mqtt connect failed",
    RET.ALIYUNMQTTERR: u"aliyun connect failed",
    RET.TXYUNMQTTERR: u"txyun connect failed",
    RET.PROTOCOLERR: u"protocol parse error",
    RET.QUECIOTERR: u"quecthing connect failed",
    RET.HWYUNERR: u"huaweiyun connect failed",
    # 功能错误
    RET.PASSWORDERR: u"password not found",
    RET.PASSWDVERIFYERR: u"password verify error",
    RET.HTTPCHANNELPARSEERR: u"http param error",
    RET.CHANNELERR: u"through channel error",
    RET.DATATYPEERR: u"data type error",
    RET.METHODERR: u"method error",
    RET.DATASENDERR: u"through data send error",
    RET.IOTTYPERR: u"mqtt type error",
    RET.NUMBERERR: u"params number error",
    RET.MODBUSERR: u"modbus prase error",
    # 数据错误
    RET.JSONLOADERR: "json load err",
    RET.JSONPARSEERR: "json parse err",
    RET.PARSEERR: "parse error",
    RET.DATAPARSEERR: "data parse error",
    RET.POINTERR: "command code error",
    RET.READFILEERR: "read file error",
    # 提醒
    RET.CMDPARSEERR: "command parse error transfer to modbus"
}

CONFIG = {
    "config_dir": "/usr",
    "config_path": "/usr/dtu_config.json",
    "backup_path": "/usr/dtu_config.json.bak",
    "config_default_path": "/usr/dtu_default_config.json"
}

HISTORY_ERROR = []

SERIAL_MAP = dict()
CHANNELS = dict()


"""=================================================  singleton  ===================================================="""

dev_imei = modem.getDevImei()


class DTUException(Exception):
    def __init__(self, message):
        self.message = message


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


"""=================================================== dtu object ==================================================="""


@Singleton
class ProdDtu(object):

    def __init__(self, dtu_gpio, uart):
        self.gpio = dtu_gpio
        self.uart = uart
        self.parse_data = DTUDocumentData()
        self.document_parser = ProdDocumentParse()
        self.channel = ChannelTransfer()
        self.offline_storage = DTUOfflineHandler()

    def prepare(self):
        while True:
            if not sim.getStatus():
                if not self.gpio.status():
                    self.gpio.show()
                utime.sleep(1)
            else:
                break

    def dialing(self):
        # 文件备份
        config_path = CONFIG["config_path"]
        config_params = ProdDocumentParse().refresh_document(config_path)
        params = ujson.loads(config_params)
        apn = params["apn"]
        print("apn: ", apn)
        call_count = 0
        if apn[0] != "" and apn[1] != "" and apn[2] != "":
            while True:
                res = dataCall.setApn(1, 0, apn[0], apn[1], apn[2], 0)
                if res == 0:
                    print("APN datacall successful")
                    break
                if res == -1:
                    print("Try APN datacall...")
                    call_count += 1
                    utime.sleep(1)
                    if call_count > 10:
                        logger.error("Datacall failed, please restart device and run again.")
                        break
        # else:
        #     while True:
        #         res = dataCall.start(1, 0, "3gnet.mnc001.mcc460.gprs", "", "", 0)
        #         if res == 0:
        #             print("datacall successful")
        #             break
        #         if res == -1:
        #             print("Try datacall...")
        #             call_count += 1
        #             utime.sleep(1)
        #             if call_count > 10:
        #                 logger.error("Datacall failed, please restart device and run again.")
        #                 break
        count = 0
        max_count = 10
        while count < max_count:
            if not dataCall.getInfo(1, 0)[2][0]:
                utime.sleep(1)
                if not self.gpio.status():
                    self.gpio.show()
                utime.sleep(1)
            else:
                break

    def parse(self):
        self.document_parser.parse(self.parse_data)

    def request(self):
        config_path = CONFIG["config_path"]
        config_params = ProdDocumentParse().refresh_document(config_path)
        try:
            ota = ujson.loads(config_params)["ota"]
        except Exception as e:
            return
        print("ota: ", ota)
        if ota[0] == "" or ota[1] == "" or ota[2] == "":
            if ota[0] == "":
                logger.info("no uid params")
            if ota[1] == "":
                logger.info("no module_type params")
            if ota[2] == "":
                logger.info("no pk params")
            print("close ota update")
            return
        # 脚本升级
        do_fota = self.parse_data.fota
        if do_fota == 1:
            if "apn_cfg.json" in uos.listdir():  # 旧版本固件
                usr = ""
            else:  # 新固件
                usr = "usr/"
            global url_zip, targetVersion, fileMD5, action, filesize
            # 获取access token
            url = "https://cloudota.quectel.com:8100/v1/oauth/token"
            imei = dev_imei
            secret = ubinascii.hexlify(uhashlib.md5("QUEC" + str(imei) + "TEL").digest())
            secret = secret.decode()
            # print(url + "?imei=" + imei + "&" + "secret=" + secret)
            resp = request.get(url + "?imei=" + imei + "&" + "secret=" + secret)
            if resp.status_code != 200:
                logger.info("***********acquire token failed!***********")
                return
            data = ""
            for i in resp.content:
                data += i.decode()
            json_data = ujson.loads(data)
            access_token = json_data["data"]["access_Token"]
            print("access_token:", access_token)
            # 升级包下载地址的请求
            version = self.parse_data.version
            moduleType = ota[1]
            download_url = "https://cloudota.quectel.com:8100/v1/fota/fw"
            headers = {"access_token": access_token, "Content-Type": "application/json"}
            acquire_data = {
                "version": str(version),
                "imei": imei,
                "moduleType": moduleType,
                "battery": 100,
                "rsrp": net.csqQueryPoll(),
                "uid": ota[0],
                "pk": ota[2]
            }
            resp = request.post(download_url, data=ujson.dumps(acquire_data), headers=headers)
            json_data = ""
            for i in resp.content:
                json_data += i.decode()
            json_data = ujson.loads(json_data)
            if json_data["code"] == 200:
                targetVersion = json_data["targetVersion"]
                url_zip = json_data["url"]
                fileMD5 = json_data["fileMd5"]
                action = json_data["action"]
                filesize = json_data["config"]["fileSize"]
                print("fileSize: ", filesize)
                print("targetVersion: ", targetVersion)
            else:
                action = json_data["action"]
                msg = json_data["msg"]
                code = json_data["code"]
                logger.info(msg)

            if action:
                report_url = "https://cloudota.quectel.com:8100/v1/fota/status/report"
                print("Please do not send instructions during the upgrade...")
                resp = request.get(url_zip)
                update_file = "dtu_handler_{}.py".format(targetVersion)
                f = open(usr + update_file, "wb+")
                count = 0
                for i in resp.content:
                    count += len(i)
                    f.write(i)
                    utime.sleep_ms(5)
                f.close()
                if filesize != count:
                    logger.info("Failed to download package data validation")
                    uos.remove(usr + "dtu_handler_V1.0.1.py")
                    #  模组状态及结果上报 升级失败，信息上报
                    data = self.data_info(version, imei, 8, "Update Failed")
                    request.post(report_url, data=ujson.dumps(data), headers=headers)
                    return
                #  模组状态及结果上报 升级成功，信息上报
                data = self.data_info(version, imei, 7, "upgrade success")
                resp = request.post(report_url, data=ujson.dumps(data), headers=headers)
                if resp.status_code == 200:
                    logger.info("The upgrade is completed and the information is reported successfully")
                else:
                    logger.info("Upgrade status information failed to be reported")
            ##################################################################################
            # 模组临终遗言信息上报
            if "system.log" not in uos.listdir(usr):
                logger.info("**********'system.log' not exist***********")
                logger.info("*********last will was not reported********")
                return
            with open(usr + "system.log", "r") as f:
                msg = f.read()
            Last_will_url = "https://cloudota.quectel.com:8100/v1/fota/msg/report"
            res = cellLocator.getLocation("www.queclocator.com", 80, "1111111122222222", 8, 1)
            data = {
                "imei": imei,
                "version": str(version),
                "signalStrength": net.csqQueryPoll(),
                "battery": 100,
                "latitude": res[0],
                "longitude": res[1],
                "details": "last will message report",
                "reportMsg": msg
            }
            headers = {"Content-Type": "application/json"}
            resp = request.post(Last_will_url, data=ujson.dumps(data), headers=headers)
            if resp.status_code == 200:
                logger.info("last will reported successfully")
            else:
                logger.info("last will was reported failed")
                return

    def data_info(self, version, imei, code, msg):
        data = {
            "version": version,
            "ver": "v1.0",
            "imei": imei,
            "code": code,
            "msg": msg
        }
        return data

    def server_filter(self):
        if self.parse_data.work_mode == 'command':
            for cid, channel in self.parse_data.conf.items():
                serial_id = int(channel.get("serialID"))
                if serial_id in self.channel.serial_channel_dict:
                    self.channel.serial_channel_dict[serial_id].append(cid)
                else:
                    self.channel.serial_channel_dict[serial_id] = [cid]
            return self.parse_data.conf
        else:
            serv_map = dict()
            serial_list = [0, 1, 2]
            for cid, channel in self.parse_data.conf.items():
                serial_id = int(channel.get("serialID"))
                if serial_id in serial_list:
                    serv_map[cid] = channel
                    self.channel.serial_channel_dict[serial_id] = [cid]
                    serial_list.remove(serial_id)
                else:
                    continue
            return serv_map

    def start(self):
        logger.info("parse data {}".format(self.parse_data.conf))
        reg_data = {"csq": net.csqQueryPoll(), "imei": dev_imei, "iccid": sim.getIccid(),
                    "ver": self.parse_data.version}  # 首次登陆服务器默认注册信息
        # 透传与modbus服务器筛选
        serv_maps = self.server_filter()
        self._serv_connect(serv_maps, reg_data)
        print("SERV conn success")
        _thread.start_new_thread(self.uart.read, ())
        if self.parse_data.offline_storage:
            _thread.start_new_thread(self.offline_storage.retry_offline_handler, ())

    def _serv_connect(self, serv_list, reg_data):
        for cid, data in serv_list.items():
            if not data:
                continue
            protocol = data.get('protocol').lower()
            if protocol == "mqtt":
                dtu_mq = DtuMqttTransfer()
                status = dtu_mq.serialize(data)
                try:
                    dtu_mq.connect()
                    _thread.start_new_thread(dtu_mq.wait, ())
                except Exception as e:
                    logger.error("{}: {}".format(error_map.get(RET.MQTTERR), e))
                else:
                    if status == RET.OK:
                        self.channel.channel_dict[cid] = dtu_mq
                        dtu_mq.channel_id = cid
                        print("mqtt conn succeed")
                    else:
                        logger.error(error_map.get(RET.MQTTERR))

            elif protocol == "aliyun":
                dtu_ali = ALYDtuMqttTransfer()
                status = dtu_ali.serialize(data)
                try:
                    _thread.start_new_thread(dtu_ali.connect, ())
                    utime.sleep_ms(100)
                except Exception as e:
                    logger.error("{}: {}".format(error_map.get(RET.ALIYUNMQTTERR), e))
                else:
                    if status == RET.OK:
                        self.channel.channel_dict[cid] = dtu_ali
                        dtu_ali.channel_id = cid
                        print("aliyun conn succeed")
                    else:
                        logger.error(error_map.get(RET.ALIYUNMQTTERR))

            elif protocol == "txyun":
                dtu_txy = TXYDtuMqttTransfer()
                status = dtu_txy.serialize(data)
                try:
                    _thread.start_new_thread(dtu_txy.connect, ())
                    utime.sleep_ms(100)
                except Exception as e:
                    logger.error("{}: {}".format(error_map.get(RET.TXYUNMQTTERR), e))
                else:
                    if status == RET.OK:
                        self.channel.channel_dict[cid] = dtu_txy
                        dtu_txy.channel_id = cid
                        print("txyun conn succeed")
                    else:
                        logger.error(error_map.get(RET.TXYUNMQTTERR))

            elif protocol == "tcp":
                tcp_sock = TcpSocket()
                status = tcp_sock.serialize(data)
                try:
                    tcp_sock.connect()
                    _thread.start_new_thread(tcp_sock.recv, ())
                except Exception as e:
                    logger.error("{}: {}".format(error_map.get(RET.TCPERR), e))
                else:
                    if status == RET.OK:
                        if self.parse_data.reg == 1:
                            tcp_sock.first_reg(reg_data)
                            logger.info("TCP send first login information {}".format(reg_data))
                        if data.get("ping"):
                            if int(data.get('heartbeat')) != 0:
                                _thread.start_new_thread(tcp_sock.Heartbeat, ())
                        self.channel.channel_dict[cid] = tcp_sock
                        tcp_sock.channel_id = cid
                    else:
                        logger.error(error_map.get(RET.TCPERR))

            elif protocol == "udp":
                udp_sock = UdpSocket()
                status = udp_sock.serialize(data)
                try:
                    udp_sock.connect()
                    _thread.start_new_thread(udp_sock.recv, ())
                except Exception as e:
                    logger.error("{}: {}".format(error_map.get(RET.UDPERR), e))
                else:
                    if status == RET.OK:
                        if self.parse_data.reg == 1:
                            udp_sock.first_reg(reg_data)
                            logger.info("UDP send first login information {}".format(reg_data))
                        if data.get("ping"):
                            if int(data.get('heartbeat')) != 0:
                                _thread.start_new_thread(udp_sock.Heartbeat, ())
                        self.channel.channel_dict[cid] = udp_sock
                        udp_sock.channel_id = cid
                    else:
                        logger.error(error_map.get(RET.UDPERR))

            elif protocol.startswith("http"):
                dtu_req = DtuRequest()
                status = dtu_req.serialize(data)
                if status == RET.OK:
                    data = dtu_req.req()  # 发送请求
                    print("***********************http request***********************")
                    for i in data:
                        print(i)
                    self.channel.channel_dict[cid] = dtu_req
                    dtu_req.channel_id = cid
                else:
                    logger.error(error_map.get(RET.HTTPERR))
            elif protocol.startswith("quecthing"):
                quec_req = QuecthingDtuTransfer()
                status = quec_req.serialize(data)
                try:
                    _thread.start_new_thread(quec_req.connect, ())
                    utime.sleep_ms(100)
                except Exception as e:
                    logger.error("{}: {}".format(error_map.get(RET.QUECIOTERR), e))
                else:
                    if status == RET.OK:
                        self.channel.channel_dict[cid] = quec_req
                        quec_req.channel_id = cid
                        print("quecthing connect waiting server...")
                    else:
                        logger.error(error_map.get(RET.QUECIOTERR))

            elif protocol.startswith("hwyun"):
                hw_req = HuaweiCloudTransfer()
                status = hw_req.serialize(data)
                try:
                    _thread.start_new_thread(hw_req.connect, ())
                    utime.sleep_ms(100)
                except Exception as e:
                    logger.error("{}: {}".format(error_map.get(RET.HWYUNERR), e))
                else:
                    if status == RET.OK:
                        self.channel.channel_dict[cid] = hw_req
                        hw_req.channel_id = cid
                        print("hwyun conn succeed")
                    else:
                        logger.error(error_map.get(RET.HWYUNERR))
            else:
                continue

@Singleton
class ProdGPIO(object):
    def __init__(self):
        # self.gpio1 = Pin(Pin.GPIO1, Pin.OUT, Pin.PULL_DISABLE, 0)
        set_gpio = False
        config_path = CONFIG["config_path"]
        config_params = ProdDocumentParse().refresh_document(config_path)
        pins = ujson.loads(config_params)["pins"]
        print("pin: ", pins)
        for i in pins:
            if len(i):
                try:
                    gpio = int(i)
                except:
                    logger.error("dtu_config.json pins setting error! Only allow numbers")
                    continue
                print("gpio {} set".format(gpio))
                gpio_n = getattr(Pin, 'GPIO%d' % gpio)
                gpio_obj = Pin(gpio_n, Pin.OUT, Pin.PULL_DISABLE, 0)
                setattr(self, "gpio%d" % gpio, gpio_obj)
                set_gpio = True

        if not set_gpio:
            self.gpio1 = Pin(Pin.GPIO1, Pin.OUT, Pin.PULL_DISABLE, 0)

    def status(self):
        self.gpio1.read()

    def show(self):
        self.gpio1.write(1)


"""===================================================socket protocol==================================================="""


class DtuRequest(object):
    _data_methods = ("PUT", "POST", "DELETE", "HEAD")

    def __init__(self):
        # self.code = code
        self.url = ""
        self.port = ""
        self.method = ""
        self.data = None
        self.serial = 0
        self.channel_id = None
        self.uart = DtuUart()
        # 用于识别连接类型
        self.conn_type = 'http'

    def serialize(self, data):
        try:
            self.method = data.get("method")
            self.url = data.get("url")
            self.data = data.get("reg_data")
            self.timeout = data.get("reg_datatimeout")
            self.serial = data.get("serialID")
            if self.method.upper() not in ["GET", "POST", "PUT", "DELETE", "HEAD"]:
                return RET.HTTPCHANNELPARSEERR
        except Exception as e:
            return RET.HTTPCHANNELPARSEERR
        else:
            return RET.OK

    # http发送的数据为json类型
    def send(self, data, *args):
        print("send data:", data)
        if isinstance(data, str):
            self.data = data
        else:
            self.data = ujson.dumps(data)
        resp_content = self.req()
        for i in resp_content:
            print(i)

    def req(self):
        global resp
        uri = self.url
        if self.port:
            uri += self.port
        try:
            if self.method.upper() in self._data_methods:
                func = getattr(request, self.method.lower())
                resp = func(uri, data=self.data)
            else:
                resp = request.get(uri, data=self.data)
        except Exception as e:
            # logger.info(e)
            logger.error("{}: {}".format(error_map.get(RET.HTTPERR), e))
            return RET.HTTPERR
        else:
            if resp.status_code == 302:
                logger.error(error_map.get(RET.REQERR1))
            if resp.status_code == 404:
                logger.error(error_map.get(RET.REQERR2))
            if resp.status_code == 500:
                logger.error(error_map.get(RET.REQERR))
            if resp.status_code == 200:
                print("HTTP RESP")
                print(resp)
                # TODO HTTP data Parse func
                rec = self.uart.output(resp.status_code, self.serial, request_id=self.channel_id)
                if isinstance(rec, dict):
                    self.send(rec)
            return resp.content

    def check_net(self):
        resp = request.get(self.url)
        return resp.status_code


class DtuSocket(object):
    def __init__(self):
        self.cli = None
        self.url = ""
        self.port = ""
        self.keep_alive = 300
        self.ping = ""
        self.heart = 60
        self.serial = 0
        # self.code = 0x00
        # self.control_channel = False
        self.dtu_uart = DtuUart()
        self.protocol = DtuProtocolData()
        self.channel_id = None
        self.conn_type = 'socket'

    def connect(self):
        sock_addr = usocket.getaddrinfo(self.url, int(self.port))[0][-1]
        logger.info("sock_addr = {}".format(sock_addr))
        self.cli.connect(sock_addr)

    def send(self, data, *args):
        try:
            print("send data:", data)
            if isinstance(data, str):
                send_data = data
            else:
                send_data = ujson.dumps(data)
            self.cli.send(send_data.encode("utf-8"))
        except Exception as e:
            logger.error("{}: {}".format(error_map.get(RET.DATAPARSEERR), e))

    def recv(self):
        while True:
            try:
                data = self.cli.recv(1024)
            except Exception as e:
                print(e)
                utime.sleep_ms(50)
                continue
            else:
                if data != b'':
                    rec = self.dtu_uart.output(data.decode(), self.serial, request_id=self.channel_id)
                    if isinstance(rec, dict):
                        self.send(rec)
                else:
                    utime.sleep_ms(50)
                    continue

    def Heartbeat(self):  # 发送心跳包
        while True:
            logger.info("send heartbeats")
            try:
                self.cli.send(self.ping.encode("utf-8"))
                logger.info("Send a heartbeat: {}".format(self.ping))
            except Exception as e:
                logger.info('send heartbeat failed !')
            print("heart time", self.heart)
            utime.sleep(self.heart)

    def first_reg(self, reg_data):  # 发送注册信息
        try:
            self.cli.send(str(reg_data).encode("utf-8"))
            # logger.info("Send first login information {}".format(reg_data))
        except Exception as e:
            logger.info('send first login information failed !{}'.format(e))

    def disconnect(self):
        self.cli.close()

    def serialize(self, data):
        try:
            self.ping = data.get("ping")
            self.heart = data.get("heartbeat")
            self.url = data.get("url")
            self.port = data.get("port")
            self.keep_alive = data.get("keepAlive", 300)
            self.serial = data.get("serialID")
        except Exception as e:
            return RET.PARSEERR
        else:
            return RET.OK

    def check_net(self):
        return self.cli.getsocketsta()


class TcpSocket(DtuSocket):

    def __init__(self):
        super(TcpSocket, self).__init__()
        # self.code = code
        self.cli = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
        self.cli.settimeout(self.keep_alive)  # 链接超时最大时间
        self.conn_type = 'tcp'


class UdpSocket(DtuSocket):

    def __init__(self):
        super(UdpSocket, self).__init__()
        # self.code = code
        self.cli = usocket.socket(usocket.AF_INET, usocket.SOCK_DGRAM)
        self.cli.settimeout(self.keep_alive)
        self.conn_type = 'udp'


class AbstractDtuMqttTransfer(object):

    def __init__(self):
        self.cli = None
        self.sub_topic = dict()
        self.pub_topic = dict()
        self.keep_alive = 300
        self.clean_session = 0
        # self.code = 0x00
        self.client_id = ""
        self.url = ""
        self.port = ""
        self.qos = 0
        self.retain = 0
        self.serial = 0
        self.product_key = ""
        self.product_secret = ""
        self.device_name = ""
        self.device_secret = ""
        self.user = ""
        self.password = ""
        # self.control_channel = False
        self.pub_topic_map = dict()
        self.sub_topic_map = dict()
        self.uart = DtuUart()
        self.channel_id = None
        self.conn_type = 'mqtt'

    def connect(self):
        self.cli.connect()

    def subscribe(self):
        for id, sub_topic in self.sub_topic.items():
            self.cli.subscribe(sub_topic)

    def publish(self, msg, topic):
        if isinstance(msg, str):
            send_msg = msg
        else:
            send_msg = ujson.dumps(msg)
        rec = self.cli.publish(topic, send_msg, qos=self.qos)

    def send(self, data, topic_id=None, *args):
        if topic_id is None:
            topic_list = self.pub_topic.keys()
            for topic in topic_list:
                self.publish(data, topic)
                print("send data:", data)
        try:
            topic = self.pub_topic.get(str(topic_id))
            self.publish(data, topic)
            print("send data:", data)
        except Exception as e:
            logger.error("{}: {}".format(error_map.get(RET.DATAPARSEERR), e))

    def callback(self, topic, msg):
        print('CallBack Msg >>>> ', topic, msg.decode())
        # 写入uart/远程控制
        rec = self.uart.output(msg.decode(), self.serial, mqtt_id=self.channel_id)
        if isinstance(rec, dict):
            if isinstance(rec, dict):
                if "topic_id" in rec:
                    topic_id = rec.pop('topic_id')
                else:
                    topic_id = list(self.pub_topic.keys())[0]
                self.send(rec, topic_id)

    def disconnect(self):
        self.cli.disconnect()

    def serialize(self, data):
        try:
            # if data[0] not in ("tas", "mos"):
            #     return RET.IOTTYPERR
            self.iot_type = data.get('type')
            self.keep_alive = int(data.get("keepAlive")) if data.get("keepAlive") else 300
            self.client_id = data.get("clientID")
            self.device_name = data.get("Devicename")
            self.product_key = data.get("ProductKey")
            self.user = data.get("user")
            self.password = data.get("password")
            if self.iot_type == "mos":
                self.device_secret = data.get('DeviceSecret') if data.get("DeviceSecret") else None
                self.product_secret = None
            else:
                self.device_secret = None
                self.product_secret = data.get('ProductSecret') if data.get('ProductSecret') else None
            clr_ses = data.get('cleanSession')
            if clr_ses in ["1", 1, True, 'true']:
                self.clean_session = True
            else:
                self.clean_session = False
            self.qos = int(data.get('qos')) if data.get('qos') else 0
            self.sub_topic = data.get('subscribe')
            self.pub_topic = data.get('publish')
            self.serial = int(data.get('serialID'))
            self.url = data.get("url")
        except Exception as e:
            logger.error(e)
            return RET.PARSEERR
        else:
            return RET.OK

    def check_net(self):
        return self.cli.get_mqttsta()


class DtuMqttTransfer(AbstractDtuMqttTransfer):
    def __init__(self):
        super().__init__()
        # self.code = code

    def connect(self):
        print("mqt connect")
        print(self.url)
        print(self.port)
        print(self.client_id)
        print(self.user)
        print(self.password)
        self.cli = MQTTClient(client_id=self.client_id, server=self.url, port=self.port,
                              user=self.user, password=self.password, keepalive=self.keep_alive)
        self.cli.set_callback(self.callback)
        self.cli.connect(clean_session=self.clean_session)
        for tid, s_topic in self.sub_topic.items():
            self.cli.subscribe(s_topic, qos=self.qos)
        for tid, p_topic in self.pub_topic.items():
            self.cli.publish(p_topic, "hello world", qos=self.qos)
        logger.info("mqtt set successful")
        # super(DtuMqttTransfer, self).connect()

    def wait(self):
        while True:
            self.cli.wait_msg()

    def serialize(self, data):
        try:
            self.client_id = data.get("clientID")
            self.keep_alive = int(data.get("keepAlive")) if data.get("keepAlive") else 60
            self.url = data.get("url")
            self.port = data.get("port")
            clr_ses = data.get('cleanSession')
            if clr_ses in ["1", 1, True, 'true']:
                self.clean_session = True
            else:
                self.clean_session = False
            self.sub_topic = data.get('subscribe')
            self.pub_topic = data.get('publish')
            self.qos = int(data.get('qos')) if data.get('qos') else 0
            self.retain = int(data.get('retain')) if data.get('retain') else 0
            self.serial = int(data.get('serialID'))
        except Exception as e:
            print(e)
            return RET.PARSEERR
        else:
            return RET.OK


class ALYDtuMqttTransfer(AbstractDtuMqttTransfer):

    def __init__(self):
        super().__init__()
        self.conn_type = 'aliyun'
        self.register_url = "https://iot-auth.cn-shanghai.aliyuncs.com/auth/register/device"
        # self.code = code

    def register(self):
        random_str = str(urandom.randint(0, 99999))
        sign_content = "deviceName%sproductKey%srandom%s" % (self.device_name, self.product_key, random_str)
        # sign = hmac_sha256(self.product_secret.encode("utf-8"), sign_content.encode("utf-8"))
        sign = hmac.new(self.product_secret.encode("utf-8"), msg=sign_content.encode("utf-8"), digestmod=uhashlib.sha256).hexdigest()
        post_data = "productKey=%s&deviceName=%s&random=%s&sign=%s&signMethod=hmacsha256" % (self.product_key, self.device_name, random_str, sign)
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        r = request.post(url=self.register_url, data=post_data, headers=headers)
        try:
            reg_msg = r.json()
            reg_data = reg_msg.get('data')
            secret_data = {self.device_name: reg_data.get("deviceSecret")}
            with open("/usr/secret.json", "w", encoding="utf-8") as w:
                ujson.dump(secret_data, w)
            print("Aliyun tas reg successful.")
        except Exception as e:
            print("Aliyun reg file write failed : %s" % str(e))

    def connect(self):
        if "secret.json" not in uos.listdir("/usr"):
            if self.iot_type == "tas":  # 一型一密
                logger.info("'secret.json' not exist")
                self.register()
            else:
                secret_data = {self.device_name: self.device_secret}
                with open("/usr/secret.json", "w", encoding="utf-8") as w:
                    ujson.dump(secret_data, w)
        self.cli = aLiYun(self.product_key, self.product_secret, self.device_name, self.device_secret)
        try:
            # 此处为了规避aliyun.py使用相对目录错误的问题
            uos.chdir("/")
            con_state = self.cli.setMqtt(self.client_id, clean_session=self.clean_session, keepAlive=self.keep_alive)
            uos.chdir("/usr/")
        except Exception as e:
            print("Aliyun conn failed")
            print(e)
            return
        if con_state == 0:
            if not self.device_secret:
                logger.info("Aliyun tas set successful")
            if not self.product_secret:
                logger.info("Aliyun mos set successful")
        if con_state == -1:
            if not self.device_secret:
                logger.info("Aliyun tas set failed")
                return
            if not self.product_secret:
                logger.info("Aliyun mos set failed")
                return
        self.cli.setCallback(self.callback)
        for tid, s_topic in self.sub_topic.items():
            self.cli.subscribe(s_topic, qos=self.qos)
        for tid, p_topic in self.pub_topic.items():
            self.cli.publish(p_topic, "hello world", qos=self.qos)
        self.cli.start()

    def check_net(self):
        return self.cli.getAliyunSta()


class TXYDtuMqttTransfer(AbstractDtuMqttTransfer):

    def __init__(self):
        super().__init__()
        self.conn_type = 'txyun'
        # self.code = code

    def connect(self):
        uos.chdir("/")
        self.cli = TXyun(self.product_key, self.device_name, self.device_secret, self.product_secret)
        if not self.device_secret:  # 一型一密
            if "tx_secret.json" not in uos.listdir("/usr"):
                logger.info("'tx_secret.json' file not exist")
                self.cli.DynamicConnectInfo()
                print("TXyun reg succeed")
                # return
        # 此处为了规避txyun.py使用相对目录错误的问题

        con_state = self.cli.setMqtt(clean_session=self.clean_session, keepAlive=self.keep_alive)
        uos.chdir("/usr/")
        if con_state == 0:
            if not self.device_secret:
                logger.info("txyun tas set successful")
            if not self.product_secret:
                logger.info("txyun mos set successful")
        if con_state == -1:
            if not self.device_secret:
                logger.info("txyun tas set failed")
                return
            if not self.product_secret:
                logger.info("txyun mos set failed")
                return
        self.cli.setCallback(self.callback)
        for tid, s_topic in self.sub_topic.items():
            self.cli.subscribe(s_topic, qos=self.qos)
        for tid, p_topic in self.pub_topic.items():
            self.cli.publish(p_topic, "hello world", qos=self.qos)
        self.cli.start()

    def check_net(self):
        return self.cli.getTXyunsta()


class QuecthingDtuTransfer:

    def __init__(self):
        self.keep_alive = 120
        self.qos = 0
        self.product_key = ""
        self.product_secret = ""
        self.send_mode = ""
        self.session_flag = 0
        self.channel_id = None
        self.serial = 0
        self.uart = DtuUart()
        self.conn_type = "quecthing"

    def connect(self):
        quecIot.init()
        quecIot.setProductinfo(self.product_key, self.product_secret)
        quecIot.setLifetime(self.keep_alive)
        quecIot.setConnmode(1)
        quecIot.setEventCB(self.callback)

    def send(self, data, pkgid=None, *args):
        if isinstance(data, str):
            send_data = data
        else:
            send_data = ujson.dumps(data)
        if self.send_mode == "pass":
            quecIot.passTransSend(self.qos, send_data)
        else:
            # 强制转换物模型dict的key`
            data_dict = dict()
            try:
                for k, v in ujson.loads(send_data).items():
                    data_dict[int(k)] = v
            except Exception as e:
                print("Quecthing data format error: %s" % e)
            if pkgid and pkgid != "0":
                quecIot.phymodelAck(self.qos, pkgid, data_dict)
            else:
                quecIot.phymodelReport(self.qos, data_dict)
        print("send data:", data)

    def callback(self, data):
        print('CallBack Msg >>>> ', data)
        if data[0] == 1:
            if data[1] == 10200:
                print("quecthing authentication succeed.")
            else:
                print("quecthing authentication failed, err code: %d" % data[1])
        if data[0] == 2:
            if data[1] == 10200:
                print("quecthing connect succeed.")
            else:
                print("quecthing connect failed, err code: %d" % data[1])
        if data[0] == 3:
            if data[1] == 10200:
                print("quecthing subscribe succeed.")
            else:
                print("quecthing subscribe failed, err code: %d" % data[1])
        if data[0] == 5:
            if data[1] == 10200:
                pkgid = 0
                msg = data[2]
            elif data[1] in [10210, 10211]:
                pkgid = data[2][0]
                msg = data[2][1]
            else:
                logger.error("Quecthing callback data error.")
                return
            rec = self.uart.output(msg.decode(), self.serial, request_id=self.channel_id, pkgid=pkgid)
            if isinstance(rec, dict):
                self.send(rec)

    def disconnect(self):
        quecIot.setConnmode(0)

    def serialize(self, data):
        try:
            self.keep_alive = int(data.get("keepAlive")) if data.get("keepAlive") else 120
            self.product_key = data.get("ProductKey")
            self.product_secret = data.get("ProductSecret")
            self.qos = int(data.get("qos", 0))
            self.session_flag = data.get("SessionFlag")
            self.send_mode = data.get("sendMode")
            self.serial = data.get("serialID")
        except Exception as e:
            logger.error(e)
            return RET.PARSEERR
        else:
            return RET.OK

    def check_net(self):
        return quecIot.getWorkState()


class HuaweiCloudTransfer(DtuMqttTransfer):

    def __init__(self):
        super().__init__()
        self.conn_type = "hwyun"
        self.device_id = ""
        self.client_id = ""
        self.user = ""
        self.password = ""


    @staticmethod
    def hmac_sha256_digest(key_K, data):

        def xor(x, y):
            return bytes(x[i] ^ y[i] for i in range(min(len(x), len(y))))

        if len(key_K) > 64:
            raise ValueError('The key must be <= 64 bytes in length')
        padded_K = key_K + b'\x00' * (64 - len(key_K))
        ipad = b'\x36' * 64
        opad = b'\x5c' * 64
        h_inner = uhashlib.sha256(xor(padded_K, ipad))
        h_inner.update(data)
        h_outer = uhashlib.sha256(xor(padded_K, opad))
        h_outer.update(h_inner.digest())
        return ubinascii.hexlify(h_outer.digest()).decode()

    def register(self):
        local_time = utime.localtime()
        time_sign = "%s%s%s%s" % (local_time[0], "%02d" % local_time[1], "%02d" % local_time[2], "%02d" % local_time[3])
        self.client_id = self.device_id + "_0_0_" + time_sign
        print("client id")
        print(self.client_id)
        self.user = self.device_id
        # self.password = hmac.new(time_sign.encode("utf-8"), self.device_secret.encode("utf-8"), digestmod=uhashlib.sha256).hexdigest()
        self.password = self.hmac_sha256_digest(time_sign.encode("utf-8"), self.device_secret.encode("utf-8"))
        print("pw")
        print(self.password)

    def serialize(self, data):
        print("hwy data")
        print(data)
        try:
            self.url = data.get("url")
            self.port = data.get("port")
            self.device_id = data.get("device_id")
            self.device_secret = data.get("secret")
            self.keep_alive = int(data.get("keepAlive")) if data.get("keepAlive") else 60
            clr_ses = data.get('cleanSession')
            if clr_ses in ["1", 1, True, 'true']:
                self.clean_session = True
            else:
                self.clean_session = False
            self.sub_topic = data.get('subscribe')
            self.pub_topic = data.get('publish')
            self.qos = int(data.get('qos')) if data.get('qos') else 0
            # self.retain = int(data.get('retain')) if data.get('retain') else 0
            self.serial = int(data.get('serialID'))
        except Exception as e:
            print("SERIAL ERR")
            print(e)
            return RET.PARSEERR
        else:
            return RET.OK

    def connect(self):
        self.register()
        print("hw connect")
        print(self.url)
        print(self.port)
        print(self.client_id)
        print(self.user)
        print(self.password)
        self.cli = MQTTClient(client_id=self.client_id, server=self.url, port=self.port,
                              user=self.user, password=self.password, keepalive=self.keep_alive, ssl=False)
        self.cli.set_callback(self.callback)
        self.cli.connect(clean_session=self.clean_session)
        for tid, s_topic in self.sub_topic.items():
            self.cli.subscribe(s_topic, qos=self.qos)
        for tid, p_topic in self.pub_topic.items():
            self.cli.publish(p_topic, "hello world", qos=self.qos)
        logger.info("hw set successful")


"""===================================================data document protocol==================================================="""


@Singleton
class DTUDocumentData(object):

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
            logger.error(e)
            logger.info("*****'dtu_config.json' not exist*****")
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
            logger.error(e)
            logger.info("*****'dtu_config.json' not exist*****")
            return


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


"""=================================================dtu handler ============================================================"""


@Singleton
class HandlerDtu(object):

    def __init__(self, dtu):
        self.dtu = dtu

    def refresh(self):
        print("refresh start")
        print(self.dtu.parse_data.auto_connect)
        if self.dtu.parse_data.auto_connect:
            print("refresh run")
            try:
                self.run()
            except Exception as e:
                print(e)
                print("Switch to backup file")
                CONFIG['config_path'] = CONFIG['config_path'] + ".bak"
                # 尝试加载备份config
                try:
                    self.run()
                except Exception as e:
                    print(e)
                    print("Switch to default file")
                    CONFIG['config_path'] = CONFIG['config_default_path']
                    # 尝试加载默认config
                    try:
                        self.run()
                    except Exception as e:
                        print(e)
                        print("default config load failed.")
        # else:
        #     pass

    def run(self):
        # try:
        self.dtu.prepare()
        print("prepart ready")
        self.dtu.dialing()
        print("dialing ready")
        self.dtu.parse()
        print("dialing parse")
        self.dtu.request()
        print("dialing request")
        self.dtu.start()
        # except Exception as e:
        #     print(e)
            # 加载bak文件
        # else:
        #     while 1:
        #         pass


@Singleton
class DtuUart(object):

    def __init__(self):
        self.dtu_d = DTUDocumentData()
        # 配置uart
        config_path = CONFIG["config_path"]
        config_params = ProdDocumentParse().refresh_document(config_path)
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
        self._direction_pin(config_params)
        self.channels = ChannelTransfer()
        self.exec_cmd = DtuExecCommand()
        self.exec_modbus = ModbusCommand()
        self.protocol = DtuProtocolData()
        self.concat_buffer = ""
        self.wait_length = 0
        self.wait_retry_count = 0

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
                if cmd_code is not None:
                    rec = self.exec_cmd.exec_command_code(cmd_code, data=msg_data, password=password)
                    print("CMD END")
                    print(rec)
                    rec['msg_id'] = msg_id
                    if mqtt_id is not None:
                        rec['topic_id'] = msg_data.get("topic_id")
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
        topic_id = mqtt_id if mqtt_id else pkgid
        package_data = self.package_datas(data, topic_id, request_id)
        uart_port.write(package_data)
        return True

    def package_datas(self, msg_data, topic_id=False, request_msg=False):
        status_code = topic_id if topic_id else request_msg
        print(msg_data)
        if len(msg_data) == 0 and request_msg:
            ret_bytes = "%s,%d".encode('utf-8') % (str(request_msg), len(msg_data))
        else:
            crc32_val = self.protocol.crc32(str(msg_data))
            msg_length = len(str(msg_data))
            ret_bytes = "%s,%s,%s,%s".encode('utf-8') % (status_code, str(msg_length), str(crc32_val), str(msg_data))
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
                if channel.conn_type in ['http', 'tcp', 'udp']:
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

    def _direction_pin(self, config_params):
        """增加输出GPIO方向控制"""
        conf = ujson.loads(config_params)
        if 'direction_pin' not in conf:
            return
        direction_pin = conf['direction_pin']
        print(direction_pin)
        for sid, conf in direction_pin.items():
            uart = self.serial_map.get(str(sid))
            gpio = getattr(Pin, "GPIO%s" % str(conf.get("GPIOn")))
            # 输出电平
            direction_level = conf.get("direction")
            uart.control_485(gpio, direction_level)


"""===================================================dtu command=========================================================="""


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
            prod_dtu = ProdDtu()
            gpio_get = getattr(prod_dtu.gpio, "gpio%s" % pins)
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
        prod_dtu = ProdDtu()
        conn_status = dict()
        for code, connect in prod_dtu.channel.channel_dict.items():
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

    def __init__(self):
        print("modbusCMD start")
        config_params = ProdDocumentParse().refresh_document(CONFIG["config_path"])
        mode = ujson.loads(config_params)['work_mode']
        if mode == "modbus":
            self.modbus_conf = ujson.loads(config_params)['modbus']
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
        self.ctf = ChannelTransfer()
        self.offline_storage = OfflineStorage()
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


@Singleton
class DTUOfflineHandler:

    def __init__(self):
        self.channels = ChannelTransfer()
        self.off_storage = OfflineStorage()

    def retry_offline_handler(self):
        while True:
            for code, channel in self.channels.channel_dict.items():
                has_msg = self.off_storage.channel_has_msg(code)
                if has_msg:
                    msg = self.off_storage.take_out(code)
                    for m in msg:
                        channel.send(m)
                else:
                    continue
            utime.sleep(20)

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


"""=================================================== run ============================================================"""


def run():
    dtu = ProdDtu(dtu_gpio=ProdGPIO(), uart=DtuUart())
    HandlerDtu(dtu).refresh()


if __name__ == '__main__':
    run()

