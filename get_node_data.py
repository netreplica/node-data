import ipdb, pprint
from nornir import InitNornir
from nornir.core.filter import F

from nornir.core.plugins.inventory import InventoryPluginRegister
from nornir_ansible.plugins.inventory.ansible import AnsibleInventory

from nornir_utils.plugins.functions import print_result
from nornir_napalm.plugins.tasks import napalm_get

InventoryPluginRegister.register("inventory", AnsibleInventory)

def nornir_connect_and_run(task, action, params, platform, username, password):
  task.host.open_connection("napalm", configuration=task.nornir.config, platform=platform, username=username, password=password)
  r = task.run(
    task=action,
    getters=params
  )
  task.host.close_connection("napalm")

# Initialize Nornir object from config_file
nr = InitNornir(config_file="config.yaml")

username="admin"
password="admin"

kinds_platforms = {
  'ceos':     'eos',
  'vr-veos':  'eos',
  'crpd':     'junos', 
  'vr-vmx':   'junos', 
  'vr-xrv9k': 'iosxr',
}

for k, v in kinds_platforms.items():
  nr = nr.filter(F(groups__contains=k))
  r = nr.run(
    task=nornir_connect_and_run,
    action=napalm_get,
    params=["facts"],
    platform=v,
    username=username,
    password=password,
  )
  for k, v in r.items():
    if not v[0].failed:
      print(f"Connection succeeded for: {k}")
      pprint.pprint(v[1].result)
    else:
      print(f"Connection failed for: {k}. Error: {v[0]}")
