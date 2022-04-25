import log
from machine import Pin
from usr.singleton import Singleton

log.basicConfig(level=log.INFO)
logger = log.getLogger(__name__)
@Singleton
class ProdGPIO(object):
    def __init__(self, pins):
        # self.gpio1 = Pin(Pin.GPIO1, Pin.OUT, Pin.PULL_DISABLE, 0)
        set_gpio = False
        print("pin: ", pins)
        for i in pins:
            if len(i):
                try:
                    gpio = int(i)
                except:
                    logger.error("dtu_config.json pins setting error! Only allow numbers")
                    continue
                print("gpio {} set".format(gpio))
                gpio_n = getattr(Pin, 'GPIO%d' % gpio)
                gpio_obj = Pin(gpio_n, Pin.OUT, Pin.PULL_DISABLE, 0)
                setattr(self, "gpio%d" % gpio, gpio_obj)
                set_gpio = True

        if not set_gpio:
            self.gpio1 = Pin(Pin.GPIO1, Pin.OUT, Pin.PULL_DISABLE, 0)

    def status(self):
        self.gpio1.read()

    def show(self):
        self.gpio1.write(1)