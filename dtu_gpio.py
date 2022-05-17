# Copyright (c) Quectel Wireless Solution, Co., Ltd.All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import utime
from machine import Pin
from usr.modules.logging import getLogger
from usr.modules.common import Singleton

log = getLogger(__name__)

class ProdGPIO(Singleton):
    def __init__(self, pins):
        # self.gpio1 = Pin(Pin.GPIO1, Pin.OUT, Pin.PULL_DISABLE, 0)
        set_gpio = False
        log.info("pin: ", pins)
        for i in pins:
            if len(i):
                try:
                    gpio = int(i)
                except:
                    log.error("dtu_config.json pins setting error! Only allow numbers")
                    continue
                log.info("gpio {} set".format(gpio))
                gpio_n = getattr(Pin, "GPIO%d" % gpio)
                gpio_obj = Pin(gpio_n, Pin.OUT, Pin.PULL_DISABLE, 0)
                setattr(self, "gpio%d" % gpio, gpio_obj)
                set_gpio = True

        if not set_gpio:
            self.gpio1 = Pin(Pin.GPIO1, Pin.OUT, Pin.PULL_DISABLE, 0)

    def status(self):
        self.gpio1.read()

    def show(self):
        self.gpio1.write(1)

    def LED_blink(self, sta, cnt):
        while(sta == 0 and cnt > 0):
            self.gpio1.write(1)
            utime.sleep(1)
            self.gpio1.write(0)
            utime.sleep(1)
            cnt -= 1