import sys, io, json

from pathlib import Path

from nornir import InitNornir
from nornir.core.filter import F

from nornir.core.plugins.inventory import InventoryPluginRegister
from nornir_ansible.plugins.inventory.ansible import AnsibleInventory

from nornir_utils.plugins.functions import print_result
from nornir_napalm.plugins.tasks import napalm_get

from nornir_scrapli.tasks import send_commands
from scrapli.driver import GenericDriver

from nornir_pygnmi.tasks import gnmi_get

InventoryPluginRegister.register("inventory", AnsibleInventory)

def nornir_connect_and_run_getters(task, plugin, action, params, platform, username, password):
  task.host.open_connection(plugin, 
                            configuration=task.nornir.config, 
                            platform=platform, 
                            username=username, 
                            password=password,
                            )
  r = task.run(
    task=action,
    getters=params,
  )
  task.host.close_connection(plugin)

def nornir_connect_and_run_commands(task, plugin, action, params, platform, username, password):
  task.host.open_connection(plugin, 
                            configuration=task.nornir.config, 
                            platform=platform, 
                            username=username, 
                            password=password,
                            extras={
                              "auth_strict_key": False,
                              "channel_log": False,
                              "comms_prompt_pattern": r".*:~#",  # see https://github.com/scrapli/nornir_scrapli/issues/132
                            },
                            )
  r = task.run(
    task=action,
    commands=params,
  )
  task.host.close_connection(plugin)

def nornir_connect_and_run_gnmi(task, plugin, action, params, platform, username, password):
  task.host.open_connection(plugin, 
                            configuration=task.nornir.config, 
                            platform=platform,
                            port=57400,
                            username=username, 
                            password=password,
                            extras={
                              "skip_verify": True,
                              "debug": False,
                            },
                           )
  r = task.run(
    task=action,
    path=params,
    encoding='JSON_IETF'
  )
  task.host.close_connection(plugin)

kinds_platforms = {
  'linux':    'generic', 
  'ceos':     'eos',
  'crpd':     'generic',
  'srl':      'srlinux',
#    'vr-veos':  'eos',
#    'vr-vmx':   'junos', 
#    'vr-xrv9k': 'iosxr',
}

kinds_credentials = {
  'linux':    {"username": "root", "password": "root"},
  'ceos':     {"username": "admin", "password": "admin"},
  'crpd':     {"username": "root", "password": "clab123"},
  'srl':      {"username": "admin",  "password": "NokiaSrl1!"},
}

kinds_tasks = {
  'linux':     nornir_connect_and_run_commands,
  'ceos':      nornir_connect_and_run_getters,
  'crpd':      nornir_connect_and_run_commands,
  'srl':       nornir_connect_and_run_gnmi,
}

kinds_plugins = {
  'linux':     "scrapli",
  'ceos':      "napalm",
  'crpd':      "scrapli",
  'srl':       "pygnmi",
}

kinds_actions = {
  'linux':     send_commands,
  'ceos':      napalm_get,
  'crpd':      send_commands,
  'srl':       gnmi_get,
}

kinds_params = {
  'linux': {
    'hostname': "cat /proc/sys/kernel/hostname",
    'domainname': "cat /proc/sys/kernel/domainname",
    'vendor': "source /etc/lsb-release; echo $DISTRIB_ID",
    'model': "echo $DISTRIB_RELEASE",
    'serial_number': "cat /sys/devices/virtual/dmi/id/product_serial",
    'os_version': "cat /proc/version",
    'uptime': "cat /proc/uptime",
    'interfaces': "ip -json address show",
  },
  'ceos': {
      'facts': "facts",
      'interfaces': "interfaces",
      'interfaces_ip': "interfaces_ip",
      'lldp_neighbors': "lldp_neighbors",
  },
  'crpd': {
    'hostname': "cat /proc/sys/kernel/hostname",
    'domainname': "cat /proc/sys/kernel/domainname",
    'vendor': "source /etc/lsb-release; echo $DISTRIB_ID",
    'model': "echo $DISTRIB_RELEASE",
    'serial_number': "cat /sys/devices/virtual/dmi/id/product_serial",
    'os_version': "cat /proc/version",
    'uptime': "cat /proc/uptime",
    'interfaces': "ip -json address show",
  },
  'srl': {
    'hostname':      "srl_nokia-system:system/srl_nokia-system-name:name/host-name",
    'domainname':    "srl_nokia-system:system/srl_nokia-system-name:name/domain-name",
    'os_version':    "srl_nokia-system:system/srl_nokia-system-info:information/version",
    'model':         "srl_nokia-platform:platform/srl_nokia-platform-chassis:chassis/type",
    'serial_number': "srl_nokia-platform:platform/srl_nokia-platform-chassis:chassis/serial-number",
    'last_booted':   "srl_nokia-system:system/srl_nokia-system-info:information/last-booted",
    #'interfaces':    "srl_nokia-interfaces:interface/ethernet/hw-mac-address",
    'interfaces':    "srl_nokia-interfaces:interface",
  },
}

# keys to extract from the data returned by the device, with normalization mapping
kinds_keys = {
    'srl': {
        'interfaces': {
            'admin-state': 'admin-state',
            'oper-state': 'oper-state',
            'description': 'description',
            'ethernet': {
                'hw-mac-address': 'mac_address',
                'port-speed': 'speed',
            },
            'mtu': 'mtu',
            'last-change': 'last-change',
        },
    }
}

def pull_data(nrinit):
  results = []
  for k, v in kinds_platforms.items():
    nr = nrinit.filter(F(groups__contains=k))
    r = nr.run(
      task=kinds_tasks[k],
      plugin=kinds_plugins[k],
      action=kinds_actions[k],
      params=list(kinds_params[k].values()),
      platform=v,
      username=kinds_credentials[k]["username"],
      password=kinds_credentials[k]["password"],
    )
    results.append({"kind": k, "result": r})
  return(results)


def parse_results_generic(kind, result):
    data = {"kind": kind}
    params = list(kinds_params[kind].keys())
    # scrapli send_commands return multi-line string as a result
    outputs = result.split("\n\n")
    if len(params) != len(outputs):
      data |= {"error": f"Number of commands and their outputs don't match"}
      return data
    collects = {}
    for i in range(0, len(params)):
      collects[params[i]] = outputs[i]
    for p, v in collects.items():
      if p == 'domainname':
        if 'hostname' in collects:
          if v == "(none)":
            data |= {'fqdn': collects['hostname']}
          else:
            data |= {'fqdn': collects['hostname'] + "." + v}
      elif p == 'os_version':
        p_split = v.split()
        # 'Linux version 5.11.0-46-generic (buildd@lgw01-amd64-010) (gcc (Ubuntu 9.3.0-17ubuntu1~20.04) 9.3.0, GNU ld (GNU Binutils for Ubuntu) 2.34) #51~20.04.1-Ubuntu SMP Fri Jan 7 06:51:40 UTC 2022'
        if v.startswith("Linux version ") and len(p_split) > 2:
          data |= {p: p_split[2]} 
      elif p == 'uptime':
        # '14165.70 54889.16'
        data |= {'uptime': float(collects['uptime'].split()[0])}
      elif p == 'interfaces':
        interfaces_array = json.loads(v)
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
        data |= {"interface_list": list(interfaces.keys())}
        data |= {"interfaces": interfaces}
        data |= {"interfaces_ip": interfaces_ip}
      else:
        data |= {p: v}
        
    return data

def parse_results_napalm(kind, result):
    data = {"kind": kind}
    for block in result:
      if block == "facts":
        data |= result["facts"] # flatten "facts"
      else:
        data |= {block: result[block]}
    
    return data

def traverse_gnmi_update(update, lookup_map, extracted_data):
    for key, val in lookup_map.items():
        if key in update.keys():
            if isinstance(val, dict):
                extracted_data |= traverse_gnmi_update(update[key], lookup_map[key], extracted_data)
            elif isinstance(val, str):
                extracted_data |= {val: update[key]}
    return extracted_data

def parse_results_gnmi_get(kind, result):
    data = {"kind": kind}
    params = list(kinds_params[kind].keys())
    paths = list(kinds_params[kind].values())
    # flatten multiple updates into one list
    updates = []
    if "notification" in result:
      for n in result["notification"]:
        if "update" in n.keys():
          for u in n["update"]:
            updates.append(u)

    for u in updates:
        if u["path"] != None and u["path"] in paths:
            # an update with path matching a query path
            i = paths.index(u["path"])
            data |= {params[i]: u["val"]}
        elif u["path"] == None:
            for k in u["val"].keys():
                # check if there is a query path with matching prefix
                for p in paths:
                    if p == k:
                        # an update with path exactly matching a query path
                        #print(k, p, u["val"][k])
                        i = paths.index(p)
                        kind_keys = kinds_keys[kind][params[i]]
                        data |= {params[i]: {}}
                        for v in u["val"][k]:
                            data_block_key = ""
                            data_block = {}
                            if "name" in v.keys():
                                data_block_key = v["name"]
                            data_block |= traverse_gnmi_update(v, kind_keys, data_block)
                            data[params[i]] |= {data_block_key: data_block}
                    elif p.startswith(k):
                        # extract path blocks to match values
                        i = paths.index(p)
                        print(k, p, params[i], u["val"][k])
                        path_blocks = p[len(k):].split("/")
                        path_blocks.insert(0, "name") # multiple entries will have different name key
                        data |= {params[i]: {}}
                        print(path_blocks)
                        for v in u["val"][k]:
                            data_block_key = ""
                            data_block = {}
                            for b in path_blocks:
                                if b == "":
                                    continue
                                elif b in v.keys():
                                    if b == "name":
                                        data_block_key = v[b]
                                    else:
                                        data_block |= {b: v[b]}
                                #print(data_block_key, data_block)
                            data[params[i]] |= {data_block_key: data_block}

    if 'hostname' in data.keys():
      if 'domainname' in data.keys() and data['domainname'] != "":
        data |= {'fqdn': data['hostname'] + "." + data['domainname']}
      else:
        data |= {'fqdn': data['hostname']}

    return data

def get_clab_node_data(root, topology, secrets=""):
  node_data = {
    "name": topology,
    "type": "node-data",
    "nodes": {},
    "errors": []
  }

  # NOTE on "clab-" prefix from https://containerlab.dev/manual/topo-def-file/#prefix
  # Even when you change the prefix, the lab directory is still uniformly named using the clab-<lab-name> pattern.
  inventory = Path(f"{root}/clab-{topology}/ansible-inventory.yml")
  default_inventory = Path(f"{root}/default/ansible-inventory.yml")
  if not(inventory.is_file()):
    if default_inventory.is_file():
      inventory = default_inventory
    else:
      node_data["errors"].append(f"No such inventory file: {inventory}")
      return(node_data)

  global kinds_credentials
  if secrets != None and secrets != "":
    try:
      with open(secrets, "r", encoding="utf-8") as f:
        try:
          kinds_credentials = json.load(f)
        except json.decoder.JSONDecodeError:
          pass
          node_data["errors"].append(f"Error parsing {secrets}")
        f.close()
    except OSError:
      pass
      node_data["errors"].append(f"Can't open secrets file: {secrets}")

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
              "hostsfile": inventory
          },
      },
  )
  
  nodes = {}
  results = pull_data(nrinit)

  for r in results:
    kind = r["kind"]
    for k, v in r["result"].items():
      if not v[0].failed:
        n = {}
        if kinds_platforms[kind] == "generic":
          n |= parse_results_generic(kind, v[1].result)
        elif kinds_platforms[kind] == "srlinux":
          n |= parse_results_gnmi_get(kind, v[1].result)
          n |= {'vendor': 'Nokia'}
        else:
          n |= parse_results_napalm(kind, v[1].result)
      else:
        n = {"kind": kind}
        n |= {"error": f"Connection failed. Error: {v[0]}"}
      nodes |= {k: n}

  node_data["nodes"] |= nodes

  return(node_data)
