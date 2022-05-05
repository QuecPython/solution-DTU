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

from usr.modules.logging import getLogger
from usr.modules.common import Observable, CloudObserver

log = getLogger(__name__)


class RemoteSubscribe(CloudObserver):
    def __init__(self):
        self.__executor = None

    def get_executor(self):
        return self.__executor

    def add_executor(self, executor):
        if executor:
            self.__executor = executor
            return True
        return False

    def raw_data(self, observable, *args, **kwargs):
        return self.__executor.cloud_data_parse(observable, *args, **kwargs) if self.__executor else False

    def object_model(self, observable, *args, **kwargs):
        return self.__executor.event_done(*args, **kwargs) if self.__executor else False

    def query(self, observable, *args, **kwargs):
        return self.__executor.event_query(*args, **kwargs) if self.__executor else False

    def ota_plain(self, observable, *args, **kwargs):
        return self.__executor.event_ota_plain(*args, **kwargs) if self.__executor else False

    def ota_file_download(self, observable, *args, **kwargs):
        # TODO: To Download OTA File For MQTT Association (Not Support Now.)
        log.debug("ota_file_download: %s" % str(args))
        if self.__executor and hasattr(self.__executor, "ota_file_download"):
            return self.__executor.event_ota_file_download(*args, **kwargs)
        else:
            return False

    def execute(self, observable, *args, **kwargs):
        """
        1. observable: Cloud Iot Object.
        2. args[1]: Cloud DownLink Data Type.
        2.1 object_model: Set Cloud Object Model.
        2.2 query: Query Cloud Object Model.
        2.3 ota_plain: OTA Plain Info.
        2.4 raw_data: Passthrough Data (Not Support Now).
        2.5 ota_file_download: Download OTA File For MQTT Association (Not Support Now).
        3. args[2]: Cloud DownLink Data(List Or Dict).
        """
        opt_attr = args[1]
        opt_args = args[2] if not isinstance(args[2], dict) else ()
        opt_kwargs = args[2] if isinstance(args[2], dict) else {}
        if hasattr(self, opt_attr):
            option_fun = getattr(self, opt_attr)
            return option_fun(observable, *opt_args, **opt_kwargs)
        else:
            log.error("RemoteSubscribe Has No Attribute [%s]." % opt_attr)
            return False


class RemotePublish(Observable):

    def __init__(self):
        """
        cloud:
            CloudIot Object
        """
        super().__init__()
        self.__cloud = None
        self.__clouds = dict()

    def __cloud_conn(self, enforce=False):
        return self.__cloud.init(enforce=enforce) if self.__cloud else False

    def __cloud_post(self, data, topic_id):
        print("test55")
        return self.__cloud.through_post_data(data, topic_id) if self.__cloud else False

    def add_cloud(self, cloud, channel_id):
        if hasattr(cloud, "init") and \
                hasattr(cloud, "post_data") and \
                hasattr(cloud, "ota_request") and \
                hasattr(cloud, "ota_action"):
            self.__clouds[channel_id] = cloud
            return True
        return False

    def cloud_ota_check(self):
        return self.__cloud.ota_request() if self.__cloud else False

    def cloud_ota_action(self, action=1, module=None):
        return self.__cloud.ota_action(action, module) if self.__cloud else False

    def cloud_device_report(self):
        return self.__cloud.device_report() if self.__cloud else False

    def post_data(self, data, channel_id, topic_id):
        """
        Data format to post:

        {
            "switch": True,
            "energy": 100,
            "non_gps": [],
            "gps": []
        }
        """
        print("test52")
        res = True
        self.__cloud = self.__clouds[channel_id]
        print("__cloud:", self.__cloud)
        if not self.__cloud_post(data, topic_id):
            print("test53")
            if self.__cloud_conn(enforce=True):
                print("test54")
                if not self.__cloud_post(data, topic_id):
                    res = False
            else:
                log.error("Cloud Connect Failed.")
                res = False
        
        if res is False:
            # This Observer Is History
            self.notifyObservers(self, *[data])

        return res
