import request
import ujson
import log

from usr.dtu_log import RET
from usr.dtu_log import error_map
log.basicConfig(level=log.INFO)
logger = log.getLogger(__name__)

class DtuRequest(object):
    _data_methods = ("PUT", "POST", "DELETE", "HEAD")

    def __init__(self, uart):
        # self.code = code
        self.url = ""
        self.port = ""
        self.method = ""
        self.data = None
        self.serial = 0
        self.channel_id = None
        self.uart = uart
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