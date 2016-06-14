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
from LagomonBase import calc_bps
from LagomonBase import calc_pps
from LagomonBase import LagomonBase
from prettytable import PrettyTable
from lagosh import ds_client

class LagoIfstats(LagomonBase):
    """
    Interface monitoring tools for lagopus vswitch.
    """
    target_name = "interfaces"

    def get_data(self, calc_throughput=False):
        """
        Get instarfaces statistics of lagopus vswitch.
        """
        n_timestamp = datetime.datetime.now()
        delta = n_timestamp - self.timestamp

        try:
            ret = ds_client().call('interface\n')
        except socket.error:
            return self.data

        self.timestamp = n_timestamp

        for ifdata in ret:
            name = ifdata[u'name']
            req = 'interface ' + name.encode() + ' stats\n'
            res = ds_client().call(req)[0]

            if calc_throughput == True:
                try:
                    rx_bps = calc_bps(res[u'rx-bytes'],
                                      self.data[name][u'rx-bytes'],
                                      delta)
                    tx_bps = calc_bps(res[u'tx-bytes'],
                                      self.data[name][u'tx-bytes'],
                                      delta)
                    rx_pps = calc_pps(res[u'rx-packets'],
                                      self.data[name][u'rx-packets'],
                                      delta)
                    tx_pps = calc_pps(res[u'tx-packets'],
                                      self.data[name][u'tx-packets'],
                                      delta)
                    res.update({u'rx_bps':rx_bps, u'rx_pps':rx_pps,
                                u'tx_bps':tx_bps, u'tx_pps':tx_pps})
                except KeyError:
                    res.update({u'rx_bps':0, u'rx_pps':0,
                                u'tx_bps':0, u'tx_pps':0})
            self.data[name] = res
        return self.data

    def monitor(self, sec=1):
        """
        Display interfaces statistics with pretty table.
        """
        rx_bps_heading = "{: ^16}".format('rx-bps')
        tx_bps_heading = "{: ^16}".format('tx-bps')
        rx_pps_heading = "{: ^12}".format('rx-pps')
        tx_pps_heading = "{: ^12}".format('tx-pps')
        table = PrettyTable([u'name',
                             rx_bps_heading,
                             rx_pps_heading,
                             tx_bps_heading,
                             tx_pps_heading])
        table.align[u'name'] = 'c'
        table.align[rx_bps_heading] = 'r'
        table.align[tx_bps_heading] = 'r'
        table.align[rx_pps_heading] = 'r'
        table.align[tx_pps_heading] = 'r'
        table.sortby = u'name'

        while self.exit_loop != True:
            self.get_data(calc_throughput=True)
            os.system('clear')
            print self.timestamp.strftime('%Y/%m/%d %H:%M:%S')
            table = table[0:0]
            for ifdata in self.data.itervalues():
                table.add_row([ifdata[u'name'],
                               '{:,}'.format(ifdata[u'rx_bps']),
                               '{:,}'.format(ifdata[u'rx_pps']),
                               '{:,}'.format(ifdata[u'tx_bps']),
                               '{:,}'.format(ifdata[u'tx_pps'])])
            print table
            time.sleep(sec)

if __name__ == "__main__":
    try:
        OPTS, ARGS = getopt.getopt(sys.argv[1:], 'l:m:')
    except getopt.GetoptError:
        sys.exit(2)

    IFSTATS = LagoIfstats()
    for opt, arg in OPTS:
        if opt == '-m':
            IFSTATS.monitor(int(arg))
        elif opt == '-l':
            IFSTATS.logger(int(arg), calc_throughput=True)

    IFSTATS.monitor()
