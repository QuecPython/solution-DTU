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

#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@file      :quecthing.py
@author    :Jack Sun (jack.sun@quectel.com)
@brief     :This file shows the interface of quecthing
@version   :0.1
@date      :2022-05-18 13:14:44
@copyright :Copyright (c) 2022
"""


import uos
import usys
import uzlib
import ql_fs
import ujson
import utime
import osTimer
import quecIot
import uhashlib
import ubinascii
import app_fota_download

from misc import Power
from queue import Queue

from usr.modules.logging import getLogger
from usr.modules.common import CloudObservable, CloudObjectModel

log = getLogger(__name__)


EVENT_CODE = {
    1: {
        10200: "Device authentication succeeded.",
        10420: "Bad request data (connection failed).",
        10422: "Device authenticated (connection failed).",
        10423: "No product information found (connection failed).",
        10424: "PAYLOAD parsing failed (connection failed).",
        10425: "Signature verification failed (connection failed).",
        10426: "Bad authentication version (connection failed).",
        10427: "Invalid hash information (connection failed).",
        10430: "PK changed (connection failed).",
        10431: "Invalid DK (connection failed).",
        10432: "PK does not match authentication version (connection failed).",
        10450: "Device internal error (connection failed).",
        10466: "Boot server address not found (connection failed).",
        10500: "Device authentication failed (an unknown exception occurred in the system).",
        10300: "Other errors.",
    },
    2: {
        10200: "Access is successful.",
        10430: "Incorrect device key (connection failed).",
        10431: "Device is disabled (connection failed).",
        10450: "Device internal error (connection failed).",
        10471: "Implementation version not supported (connection failed).",
        10473: "Abnormal access heartbeat (connection timed out).",
        10474: "Network exception (connection timed out).",
        10475: "Server changes.",
        10476: "Abnormal connection to AP.",
        10500: "Access failed (an unknown exception occurred in the system).",
    },
    3: {
        10200: "Subscription succeeded.",
        10300: "Subscription failed.",
    },
    4: {
        10200: "Transparent data sent successfully.",
        10210: "Object model data sent successfully.",
        10220: "Positioning data sent successfully.",
        10300: "Failed to send transparent data.",
        10310: "Failed to send object model data.",
        10320: "Failed to send positioning data.",
    },
    5: {
        10200: "Receive transparent data.",
        10210: "Receive data from the object model.",
        10211: "Received object model query command.",
        10473: "Received data but the length exceeds the module buffer limit, receive failed.",
        10428: "The device receives too much buffer and causes current limit.",
    },
    6: {
        10200: "Logout succeeded (disconnection succeeded).",
    },
    7: {
        10700: "New OTA plain.",
        10701: "The module starts to download.",
        10702: "Package download.",
        10703: "Package download complete.",
        10704: "Package update.",
        10705: "Firmware update complete.",
        10706: "Failed to update firmware.",
        10707: "Received confirmation broadcast.",
    },
    8: {
        10428: "High-frequency messages on the device cause current throttling.",
        10429: "Exceeds the number of activations per device or daily requests current limit.",
    }
}


class QuecObjectModel(CloudObjectModel):
    """This class is queccloud object model

    This class extend CloudObjectModel

    Attribute:
        items:
            - object model dictionary
            - data format:
            {
                "event": {
                    "name": "event",
                    "id": "",
                    "perm": "",
                    "struct_info": {
                        "name": "struct",
                        "id": "",
                        "struct_info": {
                            "key": {
                                "name": "key"
                            }
                        },
                    },
                },
                "property": {
                    "name": "event",
                    "id": "",
                    "perm": "",
                    "struct_info": {}
                }
            }
        items_id:
            - queccloud object model id and name map
            - data format
            {
                4: "energy",
                9: "power_switch",
                23: "phone_num",
            }
    """

    def __init__(self, om_file="/usr/quec_object_model.json"):
        super().__init__(om_file)
        self.items_id = {}
        self.code_id = {}
        self.id_code = {}
        self.struct_code_id = {}
        self.init()

    def __init_value(self, om_type):
        if om_type in ("int", "enum", "date"):
            om_value = 0
        elif om_type in ("float", "double"):
            om_value = 0.0
        elif om_type == "bool":
            om_value = True
        elif om_type == "text":
            om_value = ""
        elif om_type == "array":
            om_value = []
        elif om_type == "struct":
            om_value = {}
        else:
            om_value = None
        return om_value

    def __get_property(self, om_item):
        om_item_key = om_item["code"]
        om_item_type = om_item["dataType"].lower()
        om_item_val = self.__init_value(om_item_type)
        self.id_code[om_item["id"]] = om_item["code"]
        self.code_id[om_item["code"]] = om_item["id"]
        if om_item_type == "struct":
            om_item_struct = om_item["specs"]
            om_item_val = {i["code"]: self.__init_value(i["dataType"].lower()) for i in om_item_struct}
            self.struct_code_id[om_item["code"]] = {i["code"]: i["id"] for i in om_item_struct}
        return om_item_key, om_item_val

    def __init_properties(self, om_properties):
        for om_property in om_properties:
            om_property_key, om_property_val = self.__get_property(om_property)
            setattr(self.properties, om_property_key, {om_property_key: om_property_val})

    def __init_events(self, om_events):
        for om_event in om_events:
            om_event_key = om_event["code"]
            om_event_out_put = om_event.get("outputData", [])
            om_event_val = {}
            self.id_code[om_event["id"]] = om_event["code"]
            self.code_id[om_event["code"]] = om_event["id"]
            if om_event_out_put:
                for om_property in om_event_out_put:
                    property_id = int(om_property.get("$ref", "").split("/")[-1])
                    om_property_key = self.id_code.get(property_id)
                    om_property_val = getattr(self.properties, om_property_key)
                    om_property_val.update(om_property_val)
            setattr(self.events, om_event_key, {om_event_key: om_event_val})

    def init(self):
        with open(self.om_file, "rb") as f:
            cloud_object_model = ujson.load(f)
            self.__init_properties(cloud_object_model.get("properties", []))
            self.__init_events(cloud_object_model.get("events", []))


class QuecThing(CloudObservable):
    """This is a class for queccloud iot.

    This class extend CloudObservable.

    This class has the following functions:
        1. Cloud connect and disconnect
        2. Publish data to cloud
        3. Monitor data from cloud by event callback

    Run step:
        1. cloud = QuecThing(pk, ps, dk, ds, server)
        2. cloud.addObserver(RemoteSubscribe)
        3. cloud.set_object_model(QuecObjectModel)
        4. cloud.init()
        5. cloud.post_data(data)
        6. cloud.close()
    """

    def __init__(self, pk, ps, dk, ds, server, qos, life_time=120, mcu_name="", mcu_version=""):
        """
        1. Init parent class CloudObservable
        2. Init cloud connect params
        """
        super().__init__()
        self.__pk = pk
        self.__ps = ps
        self.__dk = dk
        self.__ds = ds
        self.__server = server
        self.__life_time = life_time
        self.__mcu_name = mcu_name
        self.__mcu_version = mcu_version
        self.__object_model = None
        self.__qos = qos

        self.__ota = QuecOTA()
        self.__post_result_wait_queue = Queue(maxsize=16)
        self.__quec_timer = osTimer()

    def __rm_empty_data(self, data):
        """Remove post success data item from data"""
        for k, v in data.items():
            if not v:
                del data[k]

    def __quec_timer_cb(self, args):
        """osTimer callback to break waiting of get publish result"""
        self.__put_post_res(False)

    def __get_post_res(self):
        """Get publish result"""
        self.__quec_timer.start(1000 * 10, 0, self.__quec_timer_cb)
        res = self.__post_result_wait_queue.get()
        self.__quec_timer.stop()
        return res

    def __put_post_res(self, res):
        """Save publish result to queue"""
        if self.__post_result_wait_queue.size() >= 16:
            self.__post_result_wait_queue.get()
        self.__post_result_wait_queue.put(res)

    def __data_format(self, k, v):
        """Publish data format by AliObjectModel

        Parameter:
            k: object model name
            v: object model value

        return:
            {
                "object_model_id": object_model_value
            }

        e.g.:
        k:
            "sos_alert"

        v:
            {"local_time": 1649995898000}

        return data:
            {
                6: {
                    19: 1649995898000
                }
            }
        """
        # log.debug("k: %s, v: %s" % (k, v))
        k_id = None
        struct_info = {}
        if hasattr(self.__object_model.properties, k):
            k_id = self.__object_model.code_id[k]
            if self.__object_model.struct_code_id.get(k):
                struct_info = self.__object_model.struct_code_id.get(k)
        elif hasattr(self.__object_model.events, k):
            k_id = self.__object_model.code_id[k]
            event_struct_info = hasattr(self.__object_model.events, k)
            for i in event_struct_info:
                if isinstance(getattr(self.__object_model.properties, i), dict):
                    struct_info[i] = self.__object_model.struct_code_id(i)
                else:
                    struct_info[i] = self.__object_model.code_id[i]
        else:
            return False

        log.debug("__data_format struct_info: %s" % str(struct_info))
        if isinstance(v, dict):
            nv = {}
            for ik, iv in v.items():
                if isinstance(struct_info.get(ik), int):
                    nv[struct_info[ik]] = iv
                elif isinstance(struct_info.get(ik), dict):
                    if isinstance(iv, dict):
                        nv[self.__object_model.code_id[ik]] = {struct_info[ik][ivk]: ivv for ivk, ivv in iv.items()}
                    else:
                        nv[self.__object_model.code_id[ik]] = iv
                else:
                    nv[ik] = iv
            v = nv

        return {k_id: v}

    def __event_cb(self, data):
        """Queccloud downlink message callback

        Parameter:
            data: response dictionary info, all event info see `EVENT_CODE`
            data format: (`event_code`, `errcode`, `event_data`)
                - `event_code`: event code
                - `errcode`: detail code
                - `event_data`: event data info, data type: bytes or dict
        """
        res_datas = []
        event = data[0]
        errcode = data[1]
        eventdata = b""
        if len(data) > 2:
            eventdata = data[2]
        log.info("[Event-ErrCode-Msg][%s][%s][%s] EventData[%s]" % (event, errcode, EVENT_CODE.get(event, {}).get(errcode, ""), eventdata))

        if event == 4:
            if errcode == 10200:
                self.__put_post_res(True)
            elif errcode == 10210:
                self.__put_post_res(True)
            elif errcode == 10220:
                self.__put_post_res(True)
            elif errcode == 10300:
                self.__put_post_res(False)
            elif errcode == 10310:
                self.__put_post_res(False)
            elif errcode == 10320:
                self.__put_post_res(False)
        elif event == 5:
            if errcode == 10200:
                # TODO: Data Type Passthrough (Not Support Now).
                res_data = ("raw_data", {"pkgid":0, "data":eventdata})
                res_datas.append(res_data)
            elif errcode == 10210:
                dl_data = [(self.__object_model.id_code[k], v.decode() if isinstance(v, bytes) else v) for k, v in eventdata.items()]
                res_data = ("object_model", dl_data)
                res_datas.append(res_data)
            elif errcode == 10211:
                # eventdata[0] is pkgId.
                object_model_ids = eventdata[1]
                object_model_val = [self.__object_model.id_code[i] for i in object_model_ids if self.__object_model.id_code.get(i)]
                res_data = ("query", object_model_val)
                res_datas.append(res_data)
        elif event == 7:
            if errcode == 10700:
                if eventdata:
                    file_info = eval(eventdata)
                    log.info("OTA File Info: componentNo: %s, sourceVersion: %s, targetVersion: %s, "
                             "batteryLimit: %s, minSignalIntensity: %s, useSpace: %s" % file_info)
                    res_data = ("object_model", [("ota_status", (file_info[0], 1, file_info[2]))])
                    res_datas.append(res_data)
                    ota_cfg = {
                        "componentNo": file_info[0],
                        "sourceVersion": file_info[1],
                        "targetVersion": file_info[2],
                        "batteryLimit": file_info[3],
                        "minSignalIntensity": file_info[4],
                        "useSpace": file_info[5],
                    }
                    res_data = ("ota_plain", [("ota_cfg", ota_cfg)])
                    res_datas.append(res_data)
            elif errcode == 10701:
                res_data = ("object_model", [("ota_status", (None, 2, None))])
                res_datas.append(res_data)
                file_info = eval(eventdata)
                ota_info = {
                    "componentNo": file_info[0],
                    "length": file_info[1],
                    "MD5": file_info[2],
                }
                self.__ota.set_ota_info(ota_info["length"], ota_info["MD5"])
            elif errcode == 10702:
                res_data = ("object_model", [("ota_status", (None, 2, None))])
                res_datas.append(res_data)
            elif errcode == 10703:
                res_data = ("object_model", [("ota_status", (None, 2, None))])
                res_datas.append(res_data)
                file_info = eval(eventdata)
                ota_info = {
                    "componentNo": file_info[0],
                    "length": file_info[1],
                    "startaddr": file_info[2],
                    "piece_length": file_info[3],
                }
                self.__ota.start_ota(ota_info["startaddr"], ota_info["piece_length"])
            elif errcode == 10704:
                res_data = ("object_model", [("ota_status", (None, 2, None))])
                res_datas.append(res_data)
            elif errcode == 10705:
                res_data = ("object_model", [("ota_status", (None, 3, None))])
                res_datas.append(res_data)
            elif errcode == 10706:
                res_data = ("object_model", [("ota_status", (None, 4, None))])
                res_datas.append(res_data)

        if res_datas:
            try:
                for res_data in res_datas:
                    self.notifyObservers(self, *res_data)
            except Exception as e:
                log.error("{}".format(e))

    def set_object_model(self, object_model):
        """Register QuecObjectModel to this class"""
        if object_model and isinstance(object_model, QuecObjectModel):
            self.__object_model = object_model
            return True
        return False

    def init(self, enforce=False):
        """queccloud connect

        Parameter:
            enforce:
                True: enfore cloud connect
                False: check connect status, return True if cloud connected

        Return:
            Ture: Success
            False: Failed
        """
        log.debug(
            "[init start] enforce: %s QuecThing Work State: %s, quecIot.getConnmode(): %s"
            % (enforce, quecIot.getWorkState(), quecIot.getConnmode())
        )
        log.debug("[init start] PK: %s, PS: %s, DK: %s, DS: %s, SERVER: %s" % (self.__pk, self.__ps, self.__dk, self.__ds, self.__server))
        if enforce is False:
            if self.get_status():
                return True

        quecIot.init()
        quecIot.setEventCB(self.__event_cb)
        quecIot.setProductinfo(self.__pk, self.__ps)
        if self.__dk or self.__ds:
            quecIot.setDkDs(self.__dk, self.__ds)
        quecIot.setServer(1, self.__server)
        quecIot.setLifetime(self.__life_time)
        quecIot.setMcuVersion(self.__mcu_name, self.__mcu_version)
        quecIot.setConnmode(1)

        count = 0
        while quecIot.getWorkState() != 8 and count < 10:
            utime.sleep_ms(200)
            count += 1

        if not self.__ds and self.__dk:
            count = 0
            while count < 3:
                dkds = quecIot.getDkDs()
                if dkds:
                    self.__dk, self.__ds = dkds
                    log.debug("dk: %s, ds: %s" % dkds)
                    break
                count += 1
                utime.sleep(count)

        log.debug("[init over] QuecThing Work State: %s, quecIot.getConnmode(): %s" % (quecIot.getWorkState(), quecIot.getConnmode()))
        if self.get_status():
            return True
        else:
            return False

    def close(self):
        """queccloud disconnect"""
        return quecIot.setConnmode(0)

    def get_status(self):
        """Get quectel cloud connect status

        Return:
            True -- connect success
           False -- connect falied
        """
        return True if quecIot.getWorkState() == 8 and quecIot.getConnmode() == 1 else False

    def post_data(self, data):
        """Publish object model property, event

        Parameter:
            data format:
            {
                "phone_num": "123456789",
                "energy": 100,
                "gps": [
                    "$GNGGA,XXX"
                    "$GNVTG,XXX"
                    "$GNRMC,XXX"
                ],
            }

        Return:
            Ture: Success
            False: Failed
        """
        res = True
        # log.debug("post_data: %s" % str(data))
        for k, v in data.items():
            om_data = self.__data_format(k, v)
            log.debug("post_data om_data: %s" % str(om_data))
            if om_data is not False:
                if v is not None:
                    phymodelReport_res = quecIot.phymodelReport(1, om_data)
                    if not phymodelReport_res:
                        res = False
                        break
                else:
                    continue
            elif k == "gps":
                locReportOutside_res = quecIot.locReportOutside(v)
                if not locReportOutside_res:
                    res = False
                    break
            elif k == "non_gps":
                locReportInside_res = quecIot.locReportInside(v)
                if not locReportInside_res:
                    res = False
                    break
            else:
                v = {}
                continue

            res = self.__get_post_res()
            if res:
                v = {}
            else:
                res = False
                break

        self.__rm_empty_data(data)
        return res

    def through_post_data(self, data, topic_id=None):
        try:
            pub_res = quecIot.passTransSend(self.__qos, data)
            return pub_res
        except Exception as e:
            log.error("quecthing passTransSend failed: %s. data: %s" % (e, data))
        return False

    def device_report(self):
        return quecIot.devInfoReport([i for i in range(1, 13)])

    def ota_request(self, mp_mode=0):
        """Publish mcu and firmware ota plain request

        Return:
            Ture: Success
            False: Failed
        """
        return quecIot.otaRequest(mp_mode) if mp_mode in (0, 1) else False

    def ota_action(self, action=1, module=None):
        """Publish ota upgrade start or cancel ota upgrade

        Parameter:
            action: confirm or cancel upgrade
                - 0: cancel upgrade
                - 1: confirm upgrade

            module: useless

        Return:
            Ture: Success
            False: Failed
        """
        return quecIot.otaAction(action) if action in (0, 1, 2, 3) else False


class QuecOTA(object):

    def __init__(self):
        self.__ota_file = "/usr/sotaFile.tar.gz"
        self.__updater_dir = "/usr/.updater/usr/"
        self.__file_hash = uhashlib.md5()
        self.__file_size = 0
        self.__file_md5 = ""
        self.__download_size = 0

    def __write_ota_file(self, data):
        with open(self.__ota_file, "ab+") as fp:
            fp.write(data)
            self.__file_hash.update(data)

    def __get_file_size(self, data):
        size = data.decode("ascii")
        size = size.rstrip("\0")
        if (len(size) == 0):
            return 0
        size = int(size, 8)
        return size

    def __get_file_name(self, name):
        file_name = name.decode("ascii")
        file_name = file_name.rstrip("\0")
        return file_name

    def __check_md5(self):
        file_md5 = ubinascii.hexlify(self.__file_hash.digest()).decode("ascii")
        log.debug("DMP Calc MD5 Value: %s, Device Calc MD5 Value: %s" % (self.__file_md5, file_md5))
        if (self.__file_md5 != file_md5):
            log.error("MD5 Verification Failed")
            return False

        log.debug("MD5 Verification Success.")
        return True

    def __download(self, start_addr, piece_size):
        res = 2
        readsize = 4096
        while piece_size > 0:
            readsize = readsize if readsize <= piece_size else piece_size
            updateFile = quecIot.mcuFWDataRead(start_addr, readsize)
            self.__write_ota_file(updateFile)
            log.debug("Download File Size: %s" % readsize)
            piece_size -= readsize
            start_addr += readsize
            self.__download_size += readsize
            if (self.__download_size == self.__file_size):
                log.debug("File Download Success, Update Start.")
                res = 3
                quecIot.otaAction(res)
                break
            else:
                quecIot.otaAction(res)

        return res

    def __upgrade(self):
        with open(self.__ota_file, "rb+") as ota_file:
            ota_file.seek(10)
            unzipFp = uzlib.DecompIO(ota_file, -15, 1)
            log.debug("[OTA Upgrade] Unzip file success.")
            ql_fs.mkdirs(self.__updater_dir)
            file_list = []
            try:
                while True:
                    data = unzipFp.read(0x200)
                    if not data:
                        log.debug("[OTA Upgrade] Read file size zore.")
                        break

                    size = self.__get_file_size(data[124:135])
                    file_name = self.__get_file_name(data[:100])
                    log.debug("[OTA Upgrade] File Name: %s, File Size: %s" % (file_name, size))

                    if not size:
                        if len(file_name):
                            log.debug("[OTA Upgrade] Create file: %s" % self.__updater_dir + file_name)
                            ql_fs.mkdirs(self.__updater_dir + file_name)
                        else:
                            log.debug("[OTA Upgrade] Have no file unzip.")
                            break
                    else:
                        log.debug("File %s write size %s" % (self.__updater_dir + file_name, size))
                        with open(self.__updater_dir + file_name, "wb+") as fp:
                            read_size = 0x200
                            last_size = size
                            while last_size > 0:
                                data = unzipFp.read(read_size)
                                # Calculate the actual write length
                                write_size = read_size if read_size <= last_size else last_size
                                fp.write(data[0:write_size])
                                last_size -= write_size
                            file_list.append({"file_name": "/usr/" + file_name, "size": size})

                for file_name in file_list:
                    app_fota_download.update_download_stat("/usr/.updater" + file_name["file_name"], file_name["file_name"], file_name["size"])

                log.debug("Remove %s" % self.__ota_file)
                uos.remove(self.__ota_file)

                app_fota_download.set_update_flag()
            except Exception as e:
                log.error("Unpack Error: %s" % e)
                usys.print_exception(e)
                return False

        return True

    def set_ota_info(self, size, md5):
        self.__file_size = size
        self.__file_md5 = md5

    def start_ota(self, start_addr, piece_size):
        ota_download_res = self.__download(start_addr, piece_size)
        if ota_download_res == 3:
            if self.__check_md5():
                if self.__upgrade():
                    log.debug("File Update Success, Power Restart.")
                else:
                    log.debug("File Update Failed, Power Restart.")

        Power.powerRestart()
