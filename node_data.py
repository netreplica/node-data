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

def get_clab_node_data(topology):
  # Initialize Nornir object with Containerlab ansible inventory
  nrinit = InitNornir(
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

  kinds_platforms = {
    'ceos':     'eos',
    'crpd':     'junos', 
#    'vr-veos':  'eos',
#    'vr-vmx':   'junos', 
#    'vr-xrv9k': 'iosxr',
  }

  kinds_credentials = {
    'ceos':     {"username": "admin", "password": "admin"},
    'crpd':     {"username": "root", "password": "clab123"},
  }

  kinds_getters = {
    'ceos':     ["facts", "interfaces", "lldp_neighbors"],
    #'crpd':     ["config"],
    'crpd':     [],
  }

  node_data = {
    "name": topology,
    "type": "node-data",
    "nodes": {},
  }

  nodes = {}

  for k, v in kinds_platforms.items():
    nr = nrinit.filter(F(groups__contains=k))
    r = nr.run(
      task=nornir_connect_and_run,
      plugin="napalm",
      action=napalm_get,
      params=kinds_getters[k],
      platform=v,
      username=kinds_credentials[k]["username"],
      password=kinds_credentials[k]["password"],
    )
    for k, v in r.items():
      if not v[0].failed:
        n = {}
        results = v[1].result
        for block in results:
          if block == "facts":
            n |= results["facts"] # flatten "facts"
          else:
            n |= {block: results[block]}
        nodes |= {k: n}
      else:
        return(f"Connection failed for: {k}. Error: {v[0]}")

  node_data["nodes"] |= nodes

  return(node_data)

def main():
  args = sys.argv[1:]
  print(json.dumps(get_clab_node_data(args[0])))

if __name__ == "__main__":
    main()
    
# Flask URL handler
@app.route('/collect/clab/<topology>/nodes/')
def app_clab_node_data(topology):
  t = escape(topology)
  return get_clab_node_data(t)
