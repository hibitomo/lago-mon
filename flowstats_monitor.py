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
from prettytable import PrettyTable
from lagosh import ds_client

def calc_pps(n_packets, o_packets, deltatime):
  return (n_packets - o_packets) / deltatime
def calc_pps_str(n_packets, o_packets, dletatime):
  return '{:,}'.format(calc_pps(n_packets, o_pakcets, deltatime))

def calc_bps(n_bytes, o_bytes, deltatime):
  return (n_bitcount - o_bitcounts) * 8 / deltatime
def calc_bps_str(n_bytes, o_bytes, deltatime):
  return '{:,}'.format(calc_bps(n_bytes, o_bytes, deltatime))

class lago_brstats():
  bridges = {}
  exit_loop = False
  
  def __init__(self):
    self.get_bridges()

  def get_bridges(self, calc_throughput = False):
    n_timestamp = datetime.datetime.now()
    try:
      delta = n_timestamp - self.timestamp
    except:
      delta = n_timestamp - n_timestamp
    self.timestamp = n_timestamp
    delta_sec = delta.total_seconds()

    for brdata in ds_client().call('bridge\n'):
      if calc_throughput == True:
        try:
          lps = calc_pps_str(brdata[u'flow-lookup-count'], self.bridge[brdata[u'name']][u'flow-lookup-count'], delta_sec)
          mps = calc_pps_str(brdata[u'flow-matched-count'], self.bridge[brdata[u'name']][u'flow-matched-count'], delta_sec)
          brdata.update({u'lookup_per_sec':lps, u'match_per_sec':mps})
        except:
          brdata.update({u'lookup_per_sec':'0', u'match_per_sec':'0'})
        try:
          c_rate = (brdata[u'flowcache-hit'] - self.bridge[brdata[u'name']][u'flowcache-hit']) / (brdata[u'flow-lookup-count'] - self.bridge[bridge[u'name']][u'flow-lookup-count'])
          bridge.update({u'cache_hitrate':str(c_rate)})
        except:
          brdata.update({u'cache_hitrate':'-'})
      self.bridges[brdata[u'name']] = brdata
    return self.bridges

  def monitor(self, sec = 1):
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
      self.get_bridges(calc_throughput = True)
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
    return json.dumps({u'timestamp':self.timestamp.isoformat(), u'bridges':self.bridges})

class lago_flowstats():
  flows = {}
  exit_loop = False

  def __init__(self):
    self.get_flows()

  def get_flows(self, calc_throughput = False):
    self.timestamp = datetime.datetime.now()

    for bridge in lago_brstats().bridges.itervalues():
      bridge_name = bridge[u'name']
      req = "flow " + bridge_name.encode() + ' -with-stats\n'
      res = ds_client().call(req)[0]
      self.flows[bridge_name] = res
      
    return self.flows

  def monitor(self, sec = 10):
    ptable = PrettyTable([u'priority', u'cookie', u'packet_count',
                          u'byte_count', u'data', u'actions', u'hard_timeout', u'idle_timeout'])
    ptable.align[u'priority'] = 'r'
    ptable.align[u'cookie'] = 'r'
    ptable.align[u'packet_count'] = 'r'
    ptable.align[u'byte_count'] = 'r'
    ptable.align[u'data'] = 'l'
    ptable.align[u'actions'] = 'l'
    ptable.align[u'hard_timeout'] = 'r'
    ptable.align[u'idle_timeout'] = 'r'
    ptable.sortby = u'priority'
    ptable.reversesort=True

    while self.exit_loop != True:
      os.system('clear')
      print self.timestamp.strftime('%Y/%m/%d %H:%M:%S')
      self.get_flows()
      for br_data in self.flows.itervalues():
        ptable = ptable[0:0]
        for table_data in br_data[u'tables']:
          print br_data[u'name'] + ", table: " + str(table_data[u'table'])
          for flow_data in table_data[u'flows']:
            flow = flow_data
            stats = flow.pop(u'stats')
            packet_count = "{:,}".format(stats.pop(u'packet_count'))
            byte_count = "{:,}".format(stats.pop(u'byte_count'))
            priority = flow.pop(u'priority')
            cookie = flow.pop(u'cookie')
            actions = flow.pop(u'actions')
            hard_timeout = flow.pop(u'hard_timeout')
            idle_timeout = flow.pop(u'idle_timeout')
            ptable.add_row([priority, cookie, packet_count, byte_count,
                            json.dumps(flow), json.dumps(actions), hard_timeout, idle_timeout])
          print ptable
      time.sleep(sec)

  def logger(self, sec = 1):
    while self.exit_loop != True:
      print self
      time.sleep(sec)

  def __str__(self):
    self.get_flows()
    return json.dumps({u'timestamp':self.timestamp.isoformat(), u'flows':self.flows})


if __name__ == "__main__":

  table = lago_flowstats()

  try:
    opts, args= getopt.getopt(sys.argv[1:],'l:m:')
  except getopt.GetoptError:
    sys.exit(2)
  for opt, arg in opts:
    if opt == '-m':
      table.monitor(int(arg))
    elif opt == '-l':
      table.logger(int(arg))

  table.monitor()
