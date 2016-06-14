#!/usr/bin/env python

# Copyright (C) 2014-2016 Nippon Telegraph and Telephone Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import time
import json
import datetime

def calc_pps(n_packets, o_packets, delta):
    """
    Calculate packets per second.
    """
    delta_sec = delta.total_seconds()
    return (n_packets - o_packets) / delta_sec

def calc_bps(n_bytes, o_bytes, delta):
    """
    Calculate bits per second.
    """
    delta_sec = delta.total_seconds()
    return (n_bytes - o_bytes) * 8 / delta_sec

class LagomonBase(object):
    """
    The base class of Lagopus monitoring tools
    """
    exit_loop = False
    timestamp = datetime.datetime.now()
    target_name = "lagopus"
    data = {}

    def __init__(self):
        self.get_data()

    def get_data(self, calc_throughput=False):
        """
        update statistics
        """
        pass

    def logger(self, sec=1, calc_throughput=False):
        """
        Print statistics in json
        """
        while self.exit_loop != True:
            self.get_data(calc_throughput)
            print self
            time.sleep(sec)

    def monitor(self, sec=1):
        """
        Display statistics
        """
        pass

    def __str__(self):
        return json.dumps({u'timestamp':self.timestamp.isoformat(),
                           self.target_name:self.data})
