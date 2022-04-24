import hmac
import uos
import log
import request
import uhashlib
import urandom
import ujson
from aLiYun import aLiYun
from usr.cloud import AbstractDtuMqttTransfer

log.basicConfig(level=log.INFO)
logger = log.getLogger(__name__)


class ALYDtuMqttTransfer(AbstractDtuMqttTransfer):

    def __init__(self, uart):
        super().__init__(uart)
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