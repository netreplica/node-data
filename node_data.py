import sys
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

def get_clab_node_data(topology, getters):
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
              "hostsfile": f"../clab/clab-{topology}/ansible-inventory.yml"
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
    "name": topology,
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
      params=getters,
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

def main():
  args = sys.argv[1:]
  #print(json.dumps(get_clab_node_data(args[0], ["facts", "interfaces_ip"])))
  print(json.dumps(get_clab_node_data(args[0], ["facts"])))

if __name__ == "__main__":
    main()
    
# Flask URL handler
@app.route('/collect/clab/<topology>/nodes/')
def app_clab_node_data(topology):
  t = escape(topology)
  return get_clab_node_data(t, ["facts"])
