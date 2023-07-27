"""
检查sim卡和网络状态，如有异常尝试CFUN切换或重启
"""
import net
import utime
import _thread
import checkNet
from misc import Power


class NetManager(object):
    RECONNECT_LOCK = _thread.allocate_lock()

    @classmethod
    def reconnect(cls, retry=3):
        with cls.RECONNECT_LOCK:
            for _ in range(retry):
                if cls.wait_connect():
                    return True
                cls.__cfun_switch()
            else:
                Power.powerRestart()
            return False

    @classmethod
    def wait_connect(cls, timeout=30):
        stage, state = checkNet.waitNetworkReady(timeout)
        # print('network status code: {}'.format((stage, state)))
        return stage == 3 and state == 1

    @classmethod
    def __cfun_switch(cls):
        cls.disconnect()
        utime.sleep_ms(200)
        cls.connect()

    @classmethod
    def connect(cls):
        return net.setModemFun(1, 0) == 0

    @classmethod
    def disconnect(cls):
        return net.setModemFun(0, 0) == 0
