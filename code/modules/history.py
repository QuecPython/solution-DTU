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
@file      :history.py
@author    :Jack Sun (jack.sun@quectel.com)
@brief     :Store data that fails to be sent, and send when communication is normal
@version   :0.1
@date      :2022-05-20 16:25:07
@copyright :Copyright (c) 2022
"""


import uos
import ql_fs
import ujson
import _thread

from usr.modules.logging import getLogger
from usr.modules.common import Singleton, option_lock

log = getLogger(__name__)

_history_lock = _thread.allocate_lock()


class History(Singleton):
    """This class is for manage history file."""

    def __init__(self, history_file="/usr/dtu_data.hist", max_hist_num=100):
        """
        Parameter:
            history_file: filename include full path
            max_hist_num: history data list max size
        """
        self.__history = history_file
        self.__max_hist_num = max_hist_num

    def __read_hist(self):
        """Read history file info

        Return:
            data format:
            {
                "data": [
                    {
                        "xxx": "wwww"
                    }
                ]
            }
        """
        res = {"data": []}
        if ql_fs.path_exists(self.__history):
            with open(self.__history, "r") as f:
                try:
                    hist_data = ujson.load(f)
                    if isinstance(hist_data, dict):
                        res["data"] = hist_data.get("data", [])
                except Exception:
                    pass
        return res

    def __write_hist(self, data):
        """Write data to history file

        Parameter:
        data format:
            {
                "data": [
                    {
                        "xxx": "wwww"
                    }
                ]
            }

        Return:
            True: Success
            False: Falied
        """
        try:
            with open(self.__history, "w") as f:
                ujson.dump(data, f)
                return True
        except:
            return False

    @option_lock(_history_lock)
    def read(self):
        """Read history info

        Return:
            data format:
            {
                "data": [
                    {
                        "switch": True,
                        "energy": 100,
                        "gps": ["$GPRMCx,x,x,x", "$GPGGAx,x,x,x"],
                    },
                    {
                        "switch": True,
                        "energy": 100,
                        "non_gps": ["LBS"],
                    },
                ],
            }
        """
        res = self.__read_hist()
        self.__write_hist({"data": []})
        return res

    @option_lock(_history_lock)
    def write(self, data):
        """
        Data Format For Write History:

        [
            {
                "switch": True,
                "energy": 100,
                "gps": ["$GPRMCx,x,x,x", "$GPGGAx,x,x,x"],
            },
            {
                "switch": True,
                "energy": 100,
                "non_gps": ["LBS"],
            },
        ]
        """
        res = self.__read_hist()
        res["data"].extend(data)
        if len(res["data"]) > self.__max_hist_num:
            res["data"] = res["data"][self.__max_hist_num * -1:]
        return self.__write_hist(res)

    @option_lock(_history_lock)
    def clean(self):
        try:
            uos.remove(self.__history)
            return True
        except:
            return False

    def update(self, observable, *args, **kwargs):
        return self.write(list(args[1:]))
