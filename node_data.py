import sys
import argparse
import json

from clab import *

# DEFINE GLOBAL VARs HERE

debug_on = False

def errlog(*args, **kwargs):
  print(*args, file=sys.stderr, **kwargs)

def debug(*args, **kwargs):
  if debug_on:
    errlog(*args, **kwargs)

def main():
  # CLI arguments parser
  parser = argparse.ArgumentParser(prog='node_data.py', description='Node Data API for Containerlab (experimental)')
  parser.add_argument('-r', '--root', required=True, help='root directory to search for topology subfolders')
  parser.add_argument('-t', '--topology', required=True, help='topology name to look for inventory file')
  parser.add_argument('-d', '--debug', required=False, help='enable debug output', action=argparse.BooleanOptionalAction)
  
  # Common parameters
  args = parser.parse_args()
  
  global debug_on
  debug_on = (args.debug == True)
  debug(f"DEBUG: arguments {args}")
  
  root = args.root
  topology = args.topology
  print(json.dumps(get_clab_node_data(root, topology)))

if __name__ == "__main__":
    main()

