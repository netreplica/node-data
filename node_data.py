import sys
from flask import Flask, escape, request

import json
from nornir import InitNornir
from nornir.core.filter import F

from nornir.core.plugins.inventory import InventoryPluginRegister
from nornir_ansible.plugins.inventory.ansible import AnsibleInventory

from nornir_utils.plugins.functions import print_result
from nornir_napalm.plugins.tasks import napalm_get

from nornir_scrapli.tasks import send_command
from scrapli.driver import GenericDriver

InventoryPluginRegister.register("inventory", AnsibleInventory)

app = Flask(__name__)

def nornir_connect_and_run_getters(task, plugin, action, params, platform, username, password):
  task.host.open_connection(plugin, 
                            configuration=task.nornir.config, 
                            platform=platform, 
                            username=username, 
                            password=password,
                            )
  r = task.run(
    task=action,
    getters=params
  )
  task.host.close_connection(plugin)

def nornir_connect_and_run_command(task, plugin, action, params, platform, username, password):
  task.host.open_connection(plugin, 
                            configuration=task.nornir.config, 
                            platform=platform, 
                            username=username, 
                            password=password,
                            extras={
                              "auth_strict_key": False,
                              "channel_log": False,
                            },
                            )
  r = task.run(
    task=action,
    command=params[0]
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
    'linux':    'generic', 
    'ceos':     'eos',
#    'crpd':     'generic', # TODO broken due to https://github.com/scrapli/nornir_scrapli/issues/132
#    'vr-veos':  'eos',
#    'vr-vmx':   'junos', 
#    'vr-xrv9k': 'iosxr',
  }

  kinds_credentials = {
    'linux':    {"username": "root", "password": "root"},
    'ceos':     {"username": "admin", "password": "admin"},
    'crpd':     {"username": "root", "password": "clab123"},
  }

  kinds_tasks = {
    'linux':     nornir_connect_and_run_command,
    'ceos':      nornir_connect_and_run_getters,
    'crpd':      nornir_connect_and_run_command,
  }

  kinds_plugins = {
    'linux':     "scrapli",
    'ceos':      "napalm",
    'crpd':      "scrapli",
  }

  kinds_actions = {
    'linux':     send_command,
    'ceos':      napalm_get,
    'crpd':      send_command,
  }

  kinds_params = {
    'linux':    ["ip -json address show"], # single element only
    'ceos':     ["facts", "interfaces", "lldp_neighbors", "interfaces_ip"],
    'crpd':     ["ip -json address show"], # single element only
  }
  
  node_data = {
    "name": topology,
    "type": "node-data",
    "nodes": {},
  }

  nodes = {}
  results = []

  for k, v in kinds_platforms.items():
    nr = nrinit.filter(F(groups__contains=k))
    r = nr.run(
      task=kinds_tasks[k],
      plugin=kinds_plugins[k],
      action=kinds_actions[k],
      params=kinds_params[k],
      platform=v,
      username=kinds_credentials[k]["username"],
      password=kinds_credentials[k]["password"],
    )
    results.append({"kind": k, "result": r})

  for r in results:
    kind = r["kind"]
    for k, v in r["result"].items():
      if not v[0].failed:
        n = {}
        n |= {"kind": kind}
        r = v[1].result
        if kinds_platforms[kind] == kinds_platforms["linux"]:
          interfaces_array = json.loads(r)
          interfaces = {}
          interfaces_ip = {}
          for i in interfaces_array:
            if "link_index" in i:
              if "address" in i:
                i["mac_address"] = i.pop("address").upper()
              if "addr_info" in i:
                addr_info = i.pop("addr_info")
                addr_ipv4 = {}
                addr_ipv6 = {}
                for a in addr_info:
                  if a["family"] == "inet" and "local" in a and "prefixlen" in a:
                    addr_ipv4[a["local"]] = {"prefix_length": a["prefixlen"]}
                  elif a["family"] == "inet6" and "local" in a and "prefixlen" in a:
                    addr_ipv6[a["local"]] = {"prefix_length": a["prefixlen"]}
                if len(addr_ipv4) > 0 or len(addr_ipv6) > 0:
                  interfaces_ip[i["ifname"]] = {}
                if len(addr_ipv4) > 0:
                  interfaces_ip[i["ifname"]] |= {"ipv4": addr_ipv4}
                if len(addr_ipv6) > 0:
                  interfaces_ip[i["ifname"]] |= {"ipv6": addr_ipv6}
              interfaces |= {i["ifname"]: i}
          n |= {"interface_list": list(interfaces.keys())}
          n |= {"interfaces": interfaces}
          n |= {"interfaces_ip": interfaces_ip}
        else:
          for block in r:
            if block == "facts":
              n |= r["facts"] # flatten "facts"
            else:
              n |= {block: r[block]}
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
