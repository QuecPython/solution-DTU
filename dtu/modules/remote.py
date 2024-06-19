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

import _thread
from usr.modules.logging import getLogger
from usr.modules.common import Observable, CloudObserver


log = getLogger(__name__)

class RemoteSubscribe(CloudObserver):
    """This class is for distribute cloud downlink messages"""
    def __init__(self):
        self.__executor = None

    def __raw_data(self, observable, *args, **kwargs):
        """Handle cloud transparent data transmission."""
        return self.__executor.cloud_read_data_parse_main(observable, *args, **kwargs) if self.__executor else False

    def __object_model(self, observable, *args, **kwargs):
        """Handle cloud object model setting message"""
        pass
        #return self.__executor.event_done(*args, **kwargs) if self.__executor else False

    def __query(self, observable, *args, **kwargs):
        """Handle cloud object model quering message"""
        return self.__executor.event_query(*args, **kwargs) if self.__executor else False

    def __ota_plain(self, observable, *args, **kwargs):
        """Handle cloud OTA plain"""
        return self.__executor.event_ota_plain(observable, *args, **kwargs) if self.__executor else False

    def __ota_file_download(self, observable, *args, **kwargs):
        """Handle cloud OTA file fragment download"""
        # TODO: To Download OTA File For MQTT Association (Not Support Now.)
        log.debug("ota_file_download: %s" % str(args))
        if self.__executor and hasattr(self.__executor, "ota_file_download"):
            return self.__executor.event_ota_file_download(*args, **kwargs)
        else:
            return False
    def __rrpc_request(self, *args, **kwargs):
        """RRPC request

        kwargs:
            message_id: rrpc topic message id
            data: rrpc request body
        """
        return self.__executor.rrpc_request(*args, **kwargs) if self.__executor else False

    def __thread_execute(self, option_fun, observable, opt_args, opt_kwargs):
        return option_fun(observable, *opt_args, **opt_kwargs)

    def add_executor(self, executor):
        """Add cloud downlink messages executor"""
        if executor:
            self.__executor = executor
            return True
        return False

    def execute(self, observable, *args, **kwargs):
        """Get cloud downlink messages from cloud.
        1. observable: Cloud Iot Object.
        2. args[1]: Cloud DownLink Data Type.
        2.1 object_model: Set Cloud Object Model.
        2.2 query: Query Cloud Object Model.
        2.3 ota_plain: OTA Plain Info.
        2.4 raw_data: Passthrough Data (Not Support Now).
        2.5 ota_file_download: Download OTA File For MQTT Association (Not Support Now).
        3. args[2]: Cloud DownLink Data(List Or Dict).
        """
        opt_attr = "__" + args[1]
        opt_args = args[2] if not isinstance(args[2], dict) else ()
        opt_kwargs = args[2] if isinstance(args[2], dict) else {}

        if hasattr(self, opt_attr):
            option_fun = getattr(self, opt_attr)
            _thread.start_new_thread(self.__thread_execute, (option_fun, observable, opt_args, opt_kwargs))
        else:
            log.error("RemoteSubscribe Has No Attribute [%s]." % opt_attr)


class RemotePublish(Observable):
    """This class is for post data to cloud
    Function:
        1. Check OTA plain.
        2. Confirm OTA upgrade.
        3. Device & project version report.
        4. RRPC response.
        5. Publish object model data to cloud.
    """
    def __init__(self):
        """
        cloud:
            CloudIot Object
        """
        super().__init__()
        self.__cloud = None
        self.__clouds = dict()

    def __cloud_conn(self, enforce=False):
        """Cloud connect"""
        return self.__cloud.init(enforce=enforce) if self.__cloud else False

    def __cloud_post(self, data, topic_id):
        """Cloud publish object model data"""
        try:
            return self.__cloud.through_post_data(data, topic_id) if self.__cloud else False
        except Exception as e:
            log.error("cloud post fault:", e)

    def add_cloud(self, cloud, channel_id):
        """Add Cloud object"""
        if hasattr(cloud, "init") and \
                hasattr(cloud, "post_data") and \
                hasattr(cloud, "ota_request") and \
                hasattr(cloud, "ota_action"):
            self.__clouds[channel_id] = cloud
            return True
        return False

    def cloud_ota_check(self, channel_id):
        """Check ota plain"""
        return self.__clouds[channel_id].ota_request() if self.__clouds[channel_id] else False

    def cloud_ota_action(self, channel_id, action=1, module=None):
        """Confirm ota upgrade"""
        return self.__clouds[channel_id].ota_action(action, module=module) if self.__clouds[channel_id] else False

    def cloud_device_report(self, channel_id):
        """Device & project version report"""
        return self.__clouds[channel_id].device_report() if self.__clouds[channel_id] else False

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
        res = True
        self.__cloud = self.__clouds[channel_id]
        if self.__cloud_conn():
            if not self.__cloud_post(data, topic_id):
                if self.__cloud_conn(enforce=True):
                    if not self.__cloud_post(data, topic_id):
                        res = False
                else:
                    log.error("Cloud Connect Failed.")
                    res = False
        else:
            log.error("Cloud Connect Failed.")
            res = False
        

        
        if res is False:
            # This Observer Is History
            self.notifyObservers(self, *[data])

        return res
