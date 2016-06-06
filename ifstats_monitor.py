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

class lago_ifstats():
  interfaces = {}
  exit_loop = False

  def __init__(self):
    self.get_interfaces()

  def get_interfaces(self, calc_throughput = True):
    n_timestamp = datetime.datetime.now()
    try:
      delta = n_timestamp - self.timestamp
    except:
      delta = n_timestamp - n_timestamp
    self.timestamp = n_timestamp
    delta_seconds = delta.total_seconds()

    for ifdata in ds_client().call('interface\n'):
      name = ifdata[u'name']
      req = 'interface ' + name.encode() + ' stats\n'
      res = ds_client().call(req)[0]

      if calc_throughput == True:
        try:
          rx_bps = (res[u'rx-bytes'] - interface[name][u'rx-bytes']) * 8 / delta_seconds
          tx_bps = (res[u'tx-bytes'] - interface[name][u'tx-bytes']) * 8 / delta_seconds
          rx_pps = (res[u'rx-packets'] - interface[name][u'rx-packets']) / delta_seconds
          tx_pps = (res[u'tx-packets'] - interface[name][u'tx-packets']) / delta_seconds
          rx_bps_str = '{:,}'.format(rx_bps)
          tx_bps_str = '{:,}'.format(tx_bps)
          rx_pps_str = '{:,}'.format(rx_pps)
          tx_pps_str = '{:,}'.format(tx_pps)
          res.update({u'rx_bps':rx_bps_str, u'rx_pps':rx_pps, u'tx_bps':tx_bps_str, u'tx_pps':tx_pps})
        except:
          res.update({u'rx_bps':'0', u'rx_pps':'0', u'tx_bps':'0', u'tx_pps':'0'})
      self.interfaces[name]=res
    return self.interfaces

  def monitor(self, sec = 1):
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
      os.system('clear')
      self.get_interfaces(calc_throughput = True)
      print self.timestamp.strftime('%Y/%m/%d %H:%M:%S')
      table=table[0:0]
      for ifdata in self.interfaces.itervalues():
        table.add_row([ifdata[u'name'],
                       ifdata[u'rx_bps'], ifdata[u'rx_pps'],
                       ifdata[u'tx_bps'], ifdata[u'tx_pps']])
      print table
      time.sleep(sec)

  def logger(self, sec = 1):
    while self.exit_loop != True:
      print self
      time.sleep(sec)

  def __str__(self):
    self.get_interfaces()
    return json.dumps({u'timestamp':self.timestamp.isoformat(), u'interfaces':self.interfaces})


if __name__ == "__main__":
  try:
    opts, args= getopt.getopt(sys.argv[1:],'l:m:')
  except getopt.GetoptError:
    sys.exit(2)
  table = lago_ifstats();
  for opt, arg in opts:
    if opt == '-m':
      table.monitor(int(arg))
    elif opt == '-l':
      table.logger(int(arg))

  table.monitor()


