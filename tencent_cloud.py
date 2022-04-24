import uos
import log
from TenCentYun import TXyun
from usr.cloud import AbstractDtuMqttTransfer

log.basicConfig(level=log.INFO)
logger = log.getLogger(__name__)

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
