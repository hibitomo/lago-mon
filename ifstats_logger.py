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
from lagosh import ds_client
from datetime import datetime

sec = 60
exit_loop = False
subcmd = 'interface'
stats = 'stats'

while exit_loop != True:

  log = {}
  log['@timestamp'] = datetime.now().isoformat()
  data = ds_client().call(subcmd + '\n')

  for ifdata in data:
    name = ifdata['name']
    req = subcmd + ' ' + name.encode() + ' ' + stats + '\n'
    res = ds_client().call(req)[0]
    log[name] = res

  print json.dumps(log)
  time.sleep(sec)
