import sim, uos, dataCall, ujson, net, modem, utime, _thread, uhashlib, fota, ure, ubinascii, cellLocator, request
from usr.modules.common import Singleton
from usr.modules.aliyunIot import AliYunIot, AliObjectModel
from usr.modules.quecthing import QuecThing, QuecObjectModel
from usr.modules.dtu_mqtt import DtuMqttTransfer
from usr.modules.huawei_cloud import HuaweiCloudTransfer
from usr.modules.txyunIot import TXYunIot
from usr.modules.dtu_request import DtuRequest
from usr.modules.tcp_udpsocket import TcpSocket
from usr.modules.tcp_udpsocket import UdpSocket

from usr.dtu_data_process import DtuDataProcess
from usr.settings import DTUDocumentData
from usr.settings import ProdDocumentParse
from usr.settings import CONFIG
from usr.dtu_channels import ChannelTransfer
from usr.modules.logging import RET
from usr.modules.logging import error_map
from usr.dtu_gpio import ProdGPIO
from usr.modules.remote import RemotePublish, RemoteSubscribe
from usr.modules.logging import getLogger
from usr.settings import PROJECT_NAME, PROJECT_VERSION, DEVICE_FIRMWARE_NAME, DEVICE_FIRMWARE_VERSION
from usr.dtu_protocol_data import DtuProtocolData
from usr.modules.history import History
from usr.settings import settings

log = getLogger(__name__)


class ProdDtu(Singleton):

    def __init__(self):
        self.__gpio = None
        self.__data_process = None
        self.__parse_data = None
        self.__document_parser = None
        self.__channel = None
        self.__history = None
        #self.off_storage = None
        self.__remote_sub = None
        self.__remote_pub = None

    def add_module(self, module):
        if isinstance(module, ProdGPIO):
            self.__gpio = module
            return True
        elif isinstance(module, DtuDataProcess):
            self.__data_process = module
            return True
        elif isinstance(module, DTUDocumentData):
            self.__parse_data = module
            return True
        elif isinstance(module, ProdDocumentParse):
            self.__document_parser = module
            return True
        elif isinstance(module, ChannelTransfer):
            self.__channel = module
            return True
        elif isinstance(module, History):
            self.__history = module
            return True
        elif isinstance(module, RemoteSubscribe):
            self.__remote_sub = module
            return True
        elif isinstance(module, RemotePublish):
            self.__remote_pub = module
            return True

        return False


    def prepare(self):
        while True:
            if not sim.getStatus():
                if not self.__gpio.status():
                    self.__gpio.show()
                utime.sleep(1)
            else:
                break

    def dialing(self):
        # 文件备份
        call_count = 0
        if self.__parse_data.apn[0] != "" and self.__parse_data.apn[1] != "" and self.__parse_data.apn[2] != "":
            while True:
                res = dataCall.setApn(1, 0, self.__parse_data.apn[0], self.__parse_data.apn[1], self.__parse_data.apn[2], 0)
                if res == 0:
                    log.info("APN datacall successful")
                    break
                if res == -1:
                    log.info("Try APN datacall...")
                    call_count += 1
                    utime.sleep(1)
                    if call_count > 10:
                        log.error("Datacall failed, please restart device and run again.")
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
        #                 log.error("Datacall failed, please restart device and run again.")
        #                 break
        count = 0
        max_count = 10
        while count < max_count:
            if not dataCall.getInfo(1, 0)[2][0]:
                utime.sleep(1)
                if not self.__gpio.status():
                    self.__gpio.show()
                utime.sleep(1)
            else:
                break

    def parse(self): # 更新DTUDocumentData（）
        self.__document_parser.parse(self.__parse_data)
        print(self.__parse_data.pins)

    def request(self):
        print("ota: ", self.__parse_data.ota)
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

    def start(self):
        log.info("parse data {}".format(self.__parse_data.conf))

        reg_data = {"csq": net.csqQueryPoll(), 
                    "imei": modem.getDevImei(), 
                    "iccid": sim.getIccid(),
                    "ver": self.__parse_data.version}  # 首次登陆服务器默认注册信息

        self._serv_connect(self.__channel.cloud_channel_dict, reg_data)
        print("SERV conn success")
        # 使能云端掉线历史数据记录功能后，上电之后将历史数据发出
        if settings.current_settings.get("offline_storage"):
            self.report_history()

        _thread.start_new_thread(self.__data_process.read, ())

    def _serv_connect(self, serv_list, reg_data):
        print("serv_list:",serv_list)

        for cid, data in serv_list.items():
            if not data:
                continue
            protocol = data.get("protocol").lower()
            if protocol == "mqtt":
                dtu_mq = DtuMqttTransfer(self.__data_process)
                status = dtu_mq.serialize(data)
                try:
                    dtu_mq.connect()
                    _thread.start_new_thread(dtu_mq.wait, ())
                except Exception as e:
                    log.error("{}: {}".format(error_map.get(RET.MQTTERR), e))
                else:
                    if status == RET.OK:
                        self.__channel.cloud_object_dict[cid] = dtu_mq
                        dtu_mq.channel_id = cid
                        print("mqtt conn succeed")
                    else:
                        log.error(error_map.get(RET.MQTTERR))

            elif protocol == "aliyun":
                dtu_ali = AliYunIot(data.get("ProductKey"),
                                    data.get("ProductSecret"),
                                    data.get("Devicename"),
                                    data.get("DeviceSecret"),
                                    ("%s.iot-as-mqtt.cn-shanghai.aliyuncs.com" % data.get("ProductKey")),
                                    int(data.get("qos", 0)),
                                    data.get("clientID"),
                                    data.get("publish"),
                                    data.get("subscribe"),
                                    burning_method = (1 if data.get("type") == "mos" else 0),
                                    mcu_name=PROJECT_NAME,
                                    mcu_version=PROJECT_VERSION,
                                    firmware_name=DEVICE_FIRMWARE_NAME,
                                    firmware_version=DEVICE_FIRMWARE_VERSION
                                    )
                dtu_ali.init(enforce=True)
                dtu_ali.addObserver(self.__remote_sub)
                self.__remote_pub.add_cloud(dtu_ali, cid)
                self.__channel.cloud_object_dict[cid] = dtu_ali
            elif protocol.startswith("quecthing"):
                quec_req = QuecThing(data.get("ProductKey"),
                                     data.get("ProductSecret"),
                                     data.get("Devicename"),
                                     data.get("DeviceSecret"),
                                     "iot-south.quectel.com:1883",
                                     int(data.get("qos", 0)),
                                     mcu_name=PROJECT_NAME,
                                     mcu_version=PROJECT_VERSION)
                quec_req.init(enforce=True)
                quec_req.addObserver(self.__remote_sub)
                self.__remote_pub.add_cloud(quec_req, cid)
                self.__channel.cloud_object_dict[cid] = quec_req
            elif protocol == "txyun":
                dtu_txyun = TXYunIot(data.get("ProductKey"),
                                    data.get("ProductSecret"),
                                    data.get("Devicename"),
                                    data.get("DeviceSecret"),
                                    int(data.get("cleanSession"),0),
                                    data.get("clientID"),
                                    data.get("publish"),
                                    data.get("subscribe"),
                                    burning_method = (1 if data.get("type") == "mos" else 0),
                                    mcu_name=PROJECT_NAME,
                                    mcu_version=PROJECT_VERSION,
                                    firmware_name=DEVICE_FIRMWARE_NAME,
                                    firmware_version=DEVICE_FIRMWARE_VERSION
                                    )
                dtu_txyun.init(enforce=True)
                dtu_txyun.addObserver(self.__remote_sub)
                self.__remote_pub.add_cloud(dtu_txyun, cid)
                self.__channel.cloud_object_dict[cid] = dtu_txyun

            elif protocol == "tcp":
                tcp_sock = TcpSocket(self.__data_process)
                status = tcp_sock.serialize(data)
                try:
                    tcp_sock.connect()
                    _thread.start_new_thread(tcp_sock.recv, ())
                except Exception as e:
                    log.error("{}: {}".format(error_map.get(RET.TCPERR), e))
                else:
                    if status == RET.OK:
                        if self.__parse_data.reg == 1:
                            tcp_sock.first_reg(reg_data)
                            log.info("TCP send first login information {}".format(reg_data))
                        if data.get("ping"):
                            if int(data.get("heartbeat")) != 0:
                                _thread.start_new_thread(tcp_sock.Heartbeat, ())
                        self.__channel.cloud_object_dict[cid] = tcp_sock
                        tcp_sock.channel_id = cid
                    else:
                        log.error(error_map.get(RET.TCPERR))

            elif protocol == "udp":
                udp_sock = UdpSocket()
                status = udp_sock.serialize(data)
                try:
                    udp_sock.connect(self.__data_process)
                    _thread.start_new_thread(udp_sock.recv, ())
                except Exception as e:
                    log.error("{}: {}".format(error_map.get(RET.UDPERR), e))
                else:
                    if status == RET.OK:
                        if self.__parse_data.reg == 1:
                            udp_sock.first_reg(reg_data)
                            log.info("UDP send first login information {}".format(reg_data))
                        if data.get("ping"):
                            if int(data.get("heartbeat")) != 0:
                                _thread.start_new_thread(udp_sock.Heartbeat, ())
                        self.__channel.cloud_object_dict[cid] = udp_sock
                        udp_sock.channel_id = cid
                    else:
                        log.error(error_map.get(RET.UDPERR))

            elif protocol.startswith("http"):
                dtu_req = DtuRequest()
                dtu_req.addObserver(self.__remote_sub)
                
                status = dtu_req.serialize(data)
                if status == RET.OK:
                    data = dtu_req.req()  # 发送请求
                    print("***********************http request***********************")
                    for i in data:
                        print(i)
                    self.__channel.cloud_object_dict[cid] = dtu_req
                    dtu_req.channel_id = cid
                else:
                    log.error(error_map.get(RET.HTTPERR))

            elif protocol.startswith("hwyun"):
                hw_req = HuaweiCloudTransfer(self.__data_process)
                status = hw_req.serialize(data)
                try:
                    _thread.start_new_thread(hw_req.connect, ())
                    utime.sleep_ms(100)
                except Exception as e:
                    log.error("{}: {}".format(error_map.get(RET.HWYUNERR), e))
                else:
                    if status == RET.OK:
                        self.__channel.cloud_object_dict[cid] = hw_req
                        hw_req.channel_id = cid
                        print("hwyun conn succeed")
                    else:
                        log.error(error_map.get(RET.HWYUNERR))
            else:
                continue

    def refresh(self):
        log.info("refresh start")
        if self.__parse_data.auto_connect:
            try:
                self.prepare()
                log.info("prepart ready")

                self.parse()
                log.info("dialing parse")

                self.dialing()
                log.info("dialing ready")
                
                self.request()
                log.info("dialing request")

                self.start()
            except Exception as e:
                pass
                
        # else:
        #     pass

    def report_history(self):
        if not self.__history:
            raise TypeError("self.__history is not registered.")
        if not self.__data_process:
            raise TypeError("self.__data_process is not registered.")

        res = True
        hist = self.__history.read()
        print("hist[data]:", hist["data"])

        if hist["data"]:
            pt_count = 0
            for i, data in enumerate(hist["data"]):
                pt_count += 1
                if not self.__data_process.post_hist_data(data):
                    res = False
                    break

            hist["data"] = hist["data"][pt_count:]
            if hist["data"]:
                # Flush data in hist-dictionary to tracker_data.hist file.
                self.__history.write(hist["data"])

        return res

def run():

    # 实例化通道数据
    channels = ChannelTransfer(settings.current_settings.get("work_mode"), settings.current_settings.get("conf"))
    # 实例化DTU协议数据解析方法
    dtu_protocol_data = DtuProtocolData()

    if settings.current_settings.get("offline_storage"):
        history = History()

    data_process = DtuDataProcess(settings.current_settings)

    data_process.set_channel(channels)

    data_process.set_procotol_data(dtu_protocol_data)
    
    remote_sub = RemoteSubscribe()
    remote_sub.add_executor(data_process)

    remote_pub = RemotePublish()
    if settings.current_settings.get("offline_storage"):
        remote_pub.addObserver(history)


    dtu = ProdDtu()

    dtu.add_module(ProdGPIO(settings.current_settings.get("pins")))

    dtu.add_module(data_process)

    dtu.add_module(DTUDocumentData())

    dtu.add_module(ProdDocumentParse())
    
    dtu.add_module(channels)
    if settings.current_settings.get("offline_storage"):
        dtu.add_module(history)    
    
    dtu.refresh()


if __name__ == "__main__":
    run()

