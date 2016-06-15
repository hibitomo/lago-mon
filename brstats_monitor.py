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
import datetime
import socket
import sys
import getopt
from LagomonBase import calc_pps
from LagomonBase import LagomonBase
from prettytable import PrettyTable
from lagosh import ds_client


class LagoBrstats(LagomonBase):
    """
    Bridge monitoring tools for lagopus vswitch.
    """
    target_name = "Bridges"

    def get_data(self, calc_throughput=False):
        """
        Get bridges statistics of lagopus vswitch.
        """
        n_timestamp = datetime.datetime.now()
        delta = n_timestamp - self.timestamp

        try:
            ret = ds_client().call('bridge\n')
        except socket.error:
            return self.data

        self.timestamp = n_timestamp

        for brdata in ret:
            name = brdata[u'name']
            req = 'bridge ' + name.encode() + ' stats\n'
            res = ds_client().call(req)[0]

            if calc_throughput == True:
                try:
                    lps = calc_pps(res[u'flow-lookup-count'],
                            self.data[brdata[u'name']][u'flow-lookup-count'],
                            delta)
                    mps = calc_pps(res[u'flow-matched-count'],
                            self.data[brdata[u'name']][u'flow-matched-count'],
                            delta)
                    res.update({u'lookup_per_sec':lps, u'match_per_sec':mps})
                except KeyError:
                    res.update({u'lookup_per_sec':0, u'match_per_sec':0})
                try:
                    c_hit = (res[u'flowcache-hit']
                             - self.data[brdata[u'name']][u'flowcache-hit'])
                    lookup = (res[u'flow-lookup-count']
                            - self.data[brdata[u'name']][u'flow-lookup-count'])
                    c_rate = c_hit / lookup
                    res.update({u'cache_hitrate':str(c_rate)})
                except (KeyError, ZeroDivisionError):
                    res.update({u'cache_hitrate':'-'})
            self.data[res[u'name']] = res
        return self.data

    def monitor(self, sec=1):
        """
        Display Bridges statistics with pretty table.
        """
        lps_heading = "{: ^12}".format("flow lookup/sec")
        mps_heading = "{: ^12}".format("flow match/sec")
        c_rate_heading = "{: ^5}".format("cache hit rate")
        table = PrettyTable([u'name', mps_heading, lps_heading, c_rate_heading])
        table.align[u'name'] = 'c'
        table.align[mps_heading] = 'r'
        table.align[lps_heading] = 'r'
        table.align[c_rate_heading] = 'l'
        table.sortby = u'name'

        while self.exit_loop != True:
            self.get_data(calc_throughput=True)
            os.system('clear')
            print self.timestamp.strftime('%Y/%m/%d %H:%M:%S')
            table = table[0:0]
            for brdata in self.data.itervalues():
                table.add_row([brdata[u'name'],
                               brdata[u'match_per_sec'],
                               brdata[u'lookup_per_sec'],
                               brdata[u'cache_hitrate']])
            print table
            time.sleep(sec)

if __name__ == "__main__":
    try:
        OPTS, ARGS = getopt.getopt(sys.argv[1:], 'l:m:')
    except getopt.GetoptError:
        sys.exit(2)

    BRSTATS = LagoBrstats()
    for opt, arg in OPTS:
        if opt == '-m':
            BRSTATS.monitor(int(arg))
        elif opt == '-l':
            BRSTATS.logger(int(arg), calc_throughput=True)
    BRSTATS.monitor()
