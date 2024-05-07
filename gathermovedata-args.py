#!/usr/bin/env python
import argparse
import re
from nornir_nauto_net_utils import get_the_macs_addresses, get_the_arps, enrich_node_mac_data
from simple_net_utils import node_resolve
from nautobot_credentials import nautobot_url, nautobot_token
from sitemigrate import gather_tagged_switch_data
import requests

requests.packages.urllib3.disable_warnings()

def is_valid_filename(filename):
    if not re.match(r'^[\w\-\.]+$', filename):
        return False
    return True

def main():
    parser = argparse.ArgumentParser(description="Gather tagged switch data")
    parser.add_argument("-s","--site", help="Site name", type=str, required=True)
    parser.add_argument("-t","--tag", help="Tag name", type=str, required=True)
    parser.add_argument("-hf","--hosts_filename", help="Hosts file name", type=str, required=True)

    args = parser.parse_args()

    site = args.site
    tag = args.tag
    hosts_filename = args.hosts_filename

    if not is_valid_filename(hosts_filename):
        print("Error: Invalid filename format.")
        exit(1)

    final_list = gather_tagged_switch_data(site=site, tag=tag, SAVE_RESULTS_hosts=True, hosts_filename=hosts_filename)
    return

if __name__ == "__main__":
    main()
