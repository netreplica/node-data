from flask import Flask, escape, request

import json
from nornir import InitNornir
from nornir.core.filter import F

from nornir.core.plugins.inventory import InventoryPluginRegister
from nornir_ansible.plugins.inventory.ansible import AnsibleInventory

from nornir_utils.plugins.functions import print_result
from nornir_napalm.plugins.tasks import napalm_get

InventoryPluginRegister.register("inventory", AnsibleInventory)

app = Flask(__name__)

def nornir_connect_and_run(task, plugin, action, params, platform, username, password):
  task.host.open_connection(plugin, configuration=task.nornir.config, platform=platform, username=username, password=password)
  r = task.run(
    task=action,
    getters=params
  )
  task.host.close_connection(plugin)

@app.route('/clab/<topology>/nodes/')
def get_clab_node_data(topology):
  # Initialize Nornir object with Containerlab ansible inventory
  nr = InitNornir(
      runner={
          "plugin": "threaded",
          "options": {
              "num_workers": 10,
          },
      },
      inventory={
          "plugin": "AnsibleInventory",
          "options": {
              "hostsfile": f"../clab/clab-{escape(topology)}/ansible-inventory.yml"
          },
      },
  )

  username="admin"
  password="admin"

  kinds_platforms = {
    'ceos':     'eos',
    'vr-veos':  'eos',
    'crpd':     'junos', 
    'vr-vmx':   'junos', 
    'vr-xrv9k': 'iosxr',
  }

  node_data = {
    "name": "",
    "type": "node-data",
    "nodes": {},
  }

  nodes = {}

  for k, v in kinds_platforms.items():
    nr = nr.filter(F(groups__contains=k))
    r = nr.run(
      task=nornir_connect_and_run,
      plugin="napalm",
      action=napalm_get,
      params=["facts", "interfaces_ip"],
      platform=v,
      username=username,
      password=password,
    )
    for k, v in r.items():
      if not v[0].failed:
        nodes |= {k: v[1].result}
      else:
        return(f"Connection failed for: {k}. Error: {v[0]}")

  node_data["nodes"] |= nodes

  return(node_data)