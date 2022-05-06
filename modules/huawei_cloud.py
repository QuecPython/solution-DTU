import hmac
import utime
import ubinascii
import uhashlib
import _thread

from umqtt import MQTTClient
from usr.cloud import AbstractDtuMqttTransfer
from usr.modules.logging import RET
from usr.modules.logging import getLogger

log = getLogger(__name__)


class HuaweiCloudTransfer(AbstractDtuMqttTransfer):

    def __init__(self, uart):
        super().__init__(uart)
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
            raise ValueError("The key must be <= 64 bytes in length")
        padded_K = key_K + b"\x00" * (64 - len(key_K))
        ipad = b"\x36" * 64
        opad = b"\x5c" * 64
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
            clr_ses = data.get("cleanSession")
            if clr_ses in ["1", 1, True, "true"]:
                self.clean_session = True
            else:
                self.clean_session = False
            self.sub_topic = data.get("subscribe")
            self.pub_topic = data.get("publish")
            self.qos = int(data.get("qos")) if data.get("qos") else 0
            # self.retain = int(data.get("retain")) if data.get("retain") else 0
            self.serial = int(data.get("serialID"))
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
        self.cli.connect(clean_session=self.clean_session)
        self.cli.set_callback(self.callback)
        for tid, s_topic in self.sub_topic.items():
            self.cli.subscribe(s_topic, qos=self.qos)
        for tid, p_topic in self.pub_topic.items():
            self.cli.publish(p_topic, "hello world", qos=self.qos)
        self.start_listen()
            
        log.info("hw set successful")

    def listen(self):
        while True:
            self.cli.wait_msg()
            utime.sleep_ms(100)

    def start_listen(self):
        _thread.start_new_thread(self.listen, ()) #监听线程