import quecIot
import log
import ujson
from usr.dtu_log import RET
log.basicConfig(level=log.INFO)
logger = log.getLogger(__name__)

class QuecthingDtuTransfer:

    def __init__(self, uart):
        self.keep_alive = 120
        self.qos = 0
        self.product_key = ""
        self.product_secret = ""
        self.send_mode = ""
        self.session_flag = 0
        self.channel_id = None
        self.serial = 0
        self.uart = uart
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
                parse_data = {0: data[2]}
                print("parse_data0:", parse_data)
            elif data[1] == 10210:
                parse_data = data[2]
                print("parse_data1:", parse_data)
            elif data[1] == 10211:
                pkgid = data[2][0]
                msg = data[2][1]
            else:
                logger.error("Quecthing callback data error.")
                return
            for pkgid, msg in parse_data.items():
                print("pkgid:{},msg:{}".format(pkgid, msg))
                rec = self.uart.output((msg.decode() if isinstance(msg, bytes) else msg), self.serial, request_id=self.channel_id, pkgid=pkgid)
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