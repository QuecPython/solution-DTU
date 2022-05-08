import uos
import log
import ujson
from TenCentYun import TXyun
from usr.modules.logging import getLogger
from usr.modules.common import numiter, option_lock, CloudObservable, CloudObjectModel
log = getLogger(__name__)

class TXYunIot(CloudObservable):
    """This is a class for txyun iot.

    This class extend CloudObservable.

    This class has the following functions:
        1. Cloud connect and disconnect

        2. Publish data to cloud
        2.1 Publish object module
        2.2 Publish ota device info, ota upgrade process, ota plain info request
        2.3 Publish rrpc response

        3. Subscribe data from cloud
        3.1 Subscribe publish object model result
        3.2 Subscribe cloud message
        3.3 Subscribe ota plain
        3.4 Subscribe rrpc request

    Attribute:
        ica_topic_property_post: topic for publish object model property
        ica_topic_property_post_reply: topic for subscribe publish object model property result
        ica_topic_property_set: topic for subscribe cloud object model property set
        ica_topic_event_post: topic for publish object model event
        ica_topic_event_post_reply: topic for subscribe publish object model event result
        ota_topic_device_inform: topic for publish device information
        ota_topic_device_upgrade: topic for subscribe ota plain
        ota_topic_device_progress: topic for publish ota upgrade process
        ota_topic_firmware_get: topic for publish ota plain request
        ota_topic_firmware_get_reply: topic for subscribe ota plain request response
        ota_topic_file_download: topic for publish ota mqtt file download request
        ota_topic_file_download_reply: topic for publish ota mqtt file download request response
        rrpc_topic_request: topic for subscribe rrpc message
        rrpc_topic_response: topic for publish rrpc response

    Run step:
        1. cloud = AliYunIot(pk, ps, dk, ds, server, client_id)
        2. cloud.addObserver(RemoteSubscribe)
        3. cloud.set_object_model(AliObjectModel)
        4. cloud.init()
        5. cloud.post_data(data)
        6. cloud.close()
    """
    def __init__(self, pk, ps, dk, ds, clean_session, client_id, pub_topic=None, sub_topic=None, burning_method=0, life_time=120,
                 mcu_name="", mcu_version="", firmware_name="", firmware_version="", reconn=True):
        """
        1. Init parent class CloudObservable
        2. Init cloud connect params and topic
        """
        super().__init__()
        self.conn_type = "txyun"
        self.__pk = pk
        self.__ps = ps
        self.__dk = dk
        self.__ds = ds
        self.__txyun = None
        self.__clean_session = clean_session
        self.__burning_method = burning_method
        self.__life_time = life_time
        self.__mcu_name = mcu_name
        self.__mcu_version = mcu_version
        self.__firmware_name = firmware_name
        self.__firmware_version = firmware_version
        self.__reconn = reconn
        self.__object_model = None
        self.__client_id = client_id
        self.__post_res = {}

        if pub_topic == None:
            self.pub_topic_dict = {"0": "/%s/%s/user/update" % (self.__pk, self.__dk)}
        else:
            self.pub_topic_dict = pub_topic
        if sub_topic == None:
            self.sub_topic_dict = {"0": "/%s/%s/user/get" % (self.__pk, self.__dk)}
        else:
            self.sub_topic_dict = sub_topic

    def __txyun_subscribe_topic(self):
        for id, usr_sub_topic in self.sub_topic_dict.items():
            print("usr_sub_topic:", usr_sub_topic)
            if self.__txyun.subscribe(usr_sub_topic, qos=0) == -1:
                log.error("Topic [%s] Subscribe Falied." % usr_sub_topic)


    def __txyun_sub_cb(self, topic, data):
        """Txyun subscribe topic callback

        Parameter:
            topic: topic info
            data: response dictionary info
        """
        topic = topic.decode()
        try:
            data = ujson.loads(data)
        except:
            pass

        print("test 61")
        try:
            self.notifyObservers(self, *("raw_data", {"topic":topic, "data":data} ) )
        except Exception as e:
            log.error("{}".format(e))

    def init(self, enforce=False):
        """Txyun connect and subscribe topic

        Parameter:
            enforce:
                True: enfore cloud connect and subscribe topic
                False: check connect status, return True if cloud connected

        Return:
            Ture: Success
            False: Failed
        """
        log.debug("[init start] enforce: %s" % enforce)
        if enforce is False and self.__txyun is not None:
            log.debug("self.get_status(): %s" % self.get_status())
            if self.get_status():
                return True

        if self.__txyun is not None:
            self.close()

        if self.__burning_method == 0:
            self.__ds = None
        elif self.__burning_method == 1:
            self.__ps = None
        
        log.debug("TxYun init. self.__pk: %s, self.__ps: %s, self.__dk: %s, self.__ds: %s" % (self.__pk, self.__ps, self.__dk, self.__ds))
        self.__txyun = TXyun(self.__pk, self.__dk, self.__ds, self.__ps)
        log.debug("TxYun setMqtt.")
        setMqttres = self.__txyun.setMqtt(clean_session=self.__clean_session, keepAlive=self.__life_time, reconn=self.__reconn)
        log.debug("TxYun setMqttres: %s" % setMqttres)
        if setMqttres != -1:
            setCallbackres = self.__txyun.setCallback(self.__txyun_sub_cb)
            log.debug("TxYun setCallback: %s" % setCallbackres)
            self.__txyun_subscribe_topic()
            log.debug("TxYun __txyun_subscribe_topic")
            self.__txyun.start()
            log.debug("TxYun start.")
        else:
            log.error("setMqtt Falied!")
            del self.__txyun
            self.__txyun = None
            return False

        log.debug("self.get_status(): %s" % self.get_status())
        if self.get_status():
            return True
        else:
            return False

    def close(self):
        """TxYun disconnect"""
        try:
            self.__txyun.disconnect()
        except:
            pass
        return True

    def get_status(self):
        """Get TxYun connect status

        Return:
            True -- connect success
            False -- connect falied
        """
        try:
            return True if self.__txyun.getTXyunsta() == 0 else False
        except:
            return False

    def through_post_data(self, data, topic_id):
        print("test56")
        print("topic_id type:", type(self.pub_topic_dict))
        print("self.pub_topic_dict:", self.pub_topic_dict)
        print("self.pub_topic_dict[topic_id]:", self.pub_topic_dict[topic_id])
        print("data:", data)
        try:
            pub_res = self.__txyun.publish(self.pub_topic_dict[topic_id], data, qos=0)
            print("pub_res:", pub_res)
            if pub_res == 0:
                return True
            else:
                return False
        except Exception:
            log.error("Txyun publish topic %s failed. data: %s" % (self.pub_topic_dict[topic_id], data))
        return False

    def post_data(self, data):
        pass

    def ota_request(self):
        pass

    def ota_action(self, action, module=None):
        pass