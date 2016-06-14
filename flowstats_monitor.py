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
import os
import sys
import datetime
import getopt
import socket
from prettytable import PrettyTable
from lagosh import ds_client

def calc_pps(n_packets, o_packets, deltatime):
    """
    Calculate packets per second.
    """
    return (n_packets - o_packets) / deltatime

def calc_bps(n_bytes, o_bytes, deltatime):
    """
    Calculate bits per second.
    """
    return (n_bytes - o_bytes) * 8 / deltatime

def calc_hitrate(cache_hit, lookup):
    """
    Calculate cache hit rate.
    """
    return cache_hit/lookup

class LagoBrstats(object):
    """
    Bridge monitoring tools for lagopus vswitch.
    """
    bridges = {}
    exit_loop = False
    timestamp = datetime.datetime.now()

    def __init__(self):
        self.get_bridges()

    def get_bridges(self, calc_throughput=False):
        """
        Get bridges statistics of lagopus vswitch.
        """
        n_timestamp = datetime.datetime.now()
        delta = n_timestamp - self.timestamp

        try:
            ret = ds_client().call('Bridge\n')
        except socket.error:
            return self.bridges

        self.timestamp = n_timestamp
        delta_sec = delta.total_seconds()

        for br in ret:
            if calc_throughput == True:
                try:
                    lps = calc_pps(br[u'flow-lookup-count'],
                            self.bridges[br[u'name']][u'flow-lookup-count'],
                            delta_sec)
                    mps = calc_pps(br[u'flow-matched-count'],
                            self.bridges[br[u'name']][u'flow-matched-count'],
                            delta_sec)
                    br.update({u'lookup_per_sec':lps, u'match_per_sec':mps})
                except KeyError:
                    br.update({u'lookup_per_sec':0, u'match_per_sec':0})
                try:
                    c_hit = (br[u'flowcache-hit']
                             - self.bridges[br[u'name']][u'flowcache-hit'])
                    lookup = (br[u'flow-lookup-count']
                              - self.bridges[br[u'name']][u'flow-lookup-count'])
                    c_rate = c_hit / lookup
                    br.update({u'cache_hitrate':str(c_rate)})
                except (KeyError, ZeroDivisionError):
                    br.update({u'cache_hitrate':'-'})
            self.bridges[br[u'name']] = br
        return self.bridges

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
            self.get_bridges(calc_throughput=True)
            os.system('clear')
            print self.timestamp.strftime('%Y/%m/%d %H:%M:%S')
            table = table[0:0]
            for brdata in self.bridges.itervalues():
                table.add_row([brdata[u'name'],
                               brdata[u'match_per_sec'],
                               brdata[u'lookup_per_sec'],
                               brdata[u'cache_hitrate']])
            print table
            time.sleep(sec)

    def __str__(self):
        self.get_bridges()
        return json.dumps({u'timestamp':self.timestamp.isoformat(),
                           u'bridges':self.bridges})

class LagoFlowstats(object):
    """
    Flow monitoring tools for lagopus vswitch.
    """
    flows = {}
    exit_loop = False
    timestamp = datetime.datetime.now()

    def __init__(self):
        self.get_flows()

    def get_flows(self):
        """
        Get bridges statistics of lagopus vswitch.
        """
        bridges = LagoBrstats().bridges.itervalues()
        self.timestamp = datetime.datetime.now()

        for bridge in bridges:
            bridge_name = bridge[u'name']
            req = "flow " + bridge_name.encode() + ' -with-stats\n'
            res = ds_client().call(req)[0]
            self.flows[bridge_name] = res

        return self.flows

    def monitor(self, sec=10):
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
            self.get_flows()
            for br_data in self.flows.itervalues():
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

    def logger(self, sec=1):
        """
        Print the flows statistics in json
        """
        while self.exit_loop != True:
            print self
            time.sleep(sec)

    def __str__(self):
        self.get_flows()
        return json.dumps({u'timestamp':self.timestamp.isoformat(),
                           u'flows':self.flows})


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
