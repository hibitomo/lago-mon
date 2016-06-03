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
from lagosh import ds_client
from datetime import datetime
from prettytable import PrettyTable

sec = 1
exit_loop = False
subcmd = 'interface'
stats = 'stats'
o_rx_bytes = {}
o_tx_bytes = {}
n_rx_bytes = {}
n_tx_bytes = {}
o_rx_packets = {}
o_tx_packets = {}
n_rx_packets = {}
n_tx_packets = {}
rx_bps = 0
tx_bps = 0

rx_bps_heading="{: ^16}".format('rx-bps')
tx_bps_heading="{: ^16}".format('tx-bps')
rx_pps_heading="{: ^12}".format('rx-pps')
tx_pps_heading="{: ^12}".format('tx-pps')
table=PrettyTable(['name',
                   rx_bps_heading,
                   rx_pps_heading,
                   tx_bps_heading,
                   tx_pps_heading])
table.align['name']='c'
table.align[rx_bps_heading]='r'
table.align[tx_bps_heading]='r'
table.align[rx_pps_heading]='r'
table.align[tx_pps_heading]='r'
table.sortby = "name"

while exit_loop != True:

  os.system('clear')
  print datetime.now().strftime('%Y/%m/%d %H:%M:%S')
  table=table[0:0]

  data = ds_client().call(subcmd + '\n')

  for ifdata in data:
    name = ifdata['name']
    req = subcmd + ' ' + name.encode() + ' ' + stats + '\n'
    res = ds_client().call(req)[0]
    n_rx_bytes[name] = res[u'rx-bytes']
    n_tx_bytes[name] = res[u'tx-bytes']
    n_rx_packets[name] = res[u'rx-packets']
    n_tx_packets[name] = res[u'tx-packets']

    try:
      rx_bps = (n_rx_bytes[name] - o_rx_bytes[name]) * 8 / sec
      tx_bps = (n_tx_bytes[name] - o_tx_bytes[name]) * 8 / sec
      rx_pps = n_rx_packets[name] - o_rx_packets[name]
      tx_pps = n_tx_packets[name] - o_tx_packets[name]
      rx_bps_str = '{:,}'.format(rx_bps)
      tx_bps_str = '{:,}'.format(tx_bps)
      rx_pps_str = '{:,}'.format(rx_pps)
      tx_pps_str = '{:,}'.format(tx_pps)
      table.add_row([name, rx_bps_str, rx_pps, tx_bps_str, tx_pps])
    except:
      pass

    o_rx_bytes[name] = n_rx_bytes[name]
    o_tx_bytes[name] = n_tx_bytes[name]
    o_rx_packets[name] = n_rx_packets[name]
    o_tx_packets[name] = n_tx_packets[name]

  print table
  time.sleep(sec)
