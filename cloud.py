import ujson
from umqtt import MQTTClient
from usr.modules.logging import getLogger
from usr.modules.logging import RET
from usr.modules.logging import error_map

log = getLogger(__name__)

class AbstractDtuMqttTransfer(object):

    def __init__(self, uart):
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
        self.uart = uart
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
            print("topic:", topic)
            print("send data:", data)
        except Exception as e:
            log.error("{}: {}".format(error_map.get(RET.DATAPARSEERR), e))

    def callback(self, topic, msg):
        print('CallBack Msg >>>> ', topic, msg.decode())
        # 写入uart/远程控制
        rec = self.uart.output(msg.decode(), self.serial, mqtt_id=topic, request_id=self.channel_id)
        if isinstance(rec, dict):
            if isinstance(rec, dict):
                print("rec", rec)
                if "topic_id" in rec:
                    topic_id = rec.pop('topic_id')
                    print("pop topic:", topic_id)
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
            log.error(e)
            return RET.PARSEERR
        else:
            return RET.OK

    def check_net(self):
        return self.cli.get_mqttsta()
