import usocket
import utime
import ujson

from usr.dtu_log import RET
from usr.dtu_log import error_map
from usr.modules.logging import getLogger

log = getLogger(__name__)

class DtuSocket(object):
    def __init__(self, uart):
        self.cli = None
        self.url = ""
        self.port = ""
        self.keep_alive = 300
        self.ping = ""
        self.heart = 60
        self.serial = 0
        # self.code = 0x00
        # self.control_channel = False
        self.dtu_uart = uart
        self.channel_id = None
        self.conn_type = 'socket'

    def connect(self):
        sock_addr = usocket.getaddrinfo(self.url, int(self.port))[0][-1]
        log.info("sock_addr = {}".format(sock_addr))
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
            log.error("{}: {}".format(error_map.get(RET.DATAPARSEERR), e))

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
                    print("socket data:", data)
                    """
                    rec = self.dtu_uart.output(data.decode(), self.serial, request_id=self.channel_id)
                    if isinstance(rec, dict):
                        self.send(rec)
                    """
                else:
                    utime.sleep_ms(50)
                    continue

    def Heartbeat(self):  # 发送心跳包
        while True:
            log.info("send heartbeats")
            try:
                self.cli.send(self.ping.encode("utf-8"))
                log.info("Send a heartbeat: {}".format(self.ping))
            except Exception as e:
                log.info('send heartbeat failed !')
            print("heart time", self.heart)
            utime.sleep(self.heart)

    def first_reg(self, reg_data):  # 发送注册信息
        try:
            self.cli.send(str(reg_data).encode("utf-8"))
            # log.info("Send first login information {}".format(reg_data))
        except Exception as e:
            log.info('send first login information failed !{}'.format(e))

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
