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
import os
import sys
import datetime
import getopt
import socket
import json
from brstats_monitor import LagoBrstats
from LagomonBase import LagomonBase
from prettytable import PrettyTable
from lagosh import ds_client



class LagoFlowstats(LagomonBase):
    """
    Flow monitoring tools for lagopus vswitch.
    """
    target_name = "flows"

    def get_data(self, calc_throughput=False):
        """
        Get bridges statistics of lagopus vswitch.
        """
        try:
            bridges = LagoBrstats().get_data()
        except socket.error:
            return self.data

        self.timestamp = datetime.datetime.now()

        for bridge in bridges.values():
            bridge_name = bridge[u'name']
            req = "flow " + bridge_name.encode() + ' -with-stats\n'
            res = ds_client().call(req)[0]
            self.data[bridge_name] = res
            time.sleep(.001)

        return self.data

    def monitor(self, sec=1):
        """
        Display interfaces statistics with pretty table.
        """
        ptable = PrettyTable([u'priority', u'cookie', u'packet_count',
                              u'byte_count', u'data', u'actions',
                              u'hard_timeout', u'idle_timeout'])
        ptable.align[u'priority'] = 'r'
        ptable.align[u'cookie'] = 'r'
        ptable.align[u'packet_count'] = 'r'
        ptable.align[u'byte_count'] = 'r'
        ptable.align[u'data'] = 'l'
        ptable.align[u'actions'] = 'l'
        ptable.align[u'hard_timeout'] = 'r'
        ptable.align[u'idle_timeout'] = 'r'
        ptable.sortby = u'priority'
        ptable.reversesort = True

        while self.exit_loop != True:
            os.system('clear')
            print self.timestamp.strftime('%Y/%m/%d %H:%M:%S')
            self.get_data()
            for br_data in self.data.itervalues():
                ptable = ptable[0:0]
                for table in br_data[u'tables']:
                    print br_data[u'name'] + ", table: " + str(table[u'table'])
                    for flow_data in table[u'flows']:
                        flow = flow_data
                        stats = flow.pop(u'stats')
                        packet_count = "{:,}".format(stats.pop(u'packet_count'))
                        byte_count = "{:,}".format(stats.pop(u'byte_count'))
                        priority = flow.pop(u'priority')
                        cookie = flow.pop(u'cookie')
                        actions = flow.pop(u'actions')
                        hard_timeout = flow.pop(u'hard_timeout')
                        idle_timeout = flow.pop(u'idle_timeout')
                        ptable.add_row([priority, cookie,
                                        packet_count, byte_count,
                                        json.dumps(flow), json.dumps(actions),
                                        hard_timeout, idle_timeout])
                    print ptable
            time.sleep(sec)

if __name__ == "__main__":

    FLOWSTATS = LagoFlowstats()

    try:
        OPTS, ARGS = getopt.getopt(sys.argv[1:], 'l:m:')
    except getopt.GetoptError:
        sys.exit(2)
    for opt, arg in OPTS:
        if opt == '-m':
            FLOWSTATS.monitor(int(arg))
        elif opt == '-l':
            FLOWSTATS.logger(int(arg))

    FLOWSTATS.monitor()
