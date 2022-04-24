import log
from umqtt import MQTTClient
from usr.cloud import AbstractDtuMqttTransfer
from usr.dtu_log import RET


log.basicConfig(level=log.INFO)
logger = log.getLogger(__name__)

class DtuMqttTransfer(AbstractDtuMqttTransfer):
    def __init__(self, uart):
        super().__init__(uart)
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