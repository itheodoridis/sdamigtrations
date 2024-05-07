#!/usr/bin/env python
from nornir_nauto_net_utils import compare_hosts_list, speak_to_the_team
from simple_net_utils import load_hosts_list
from sitemigrate import gather_tagged_switch_data
from nautobot_credentials import nautobot_url, nautobot_token
from msteams_credentials import msteams_webhook_url
import argparse
import re
import os

def is_valid_filename(filename):
    if not re.match(r'^[\w\-\.]+$', filename):
        return False
    return True

def file_exists(filename):
    return os.path.exists(filename)

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

    if not file_exists(hosts_filename):
        print(f"Error: File '{hosts_filename}' does not exist.")
        exit(1)

    final_list = gather_tagged_switch_data(site=site, tag=tag)
    stored_hosts = load_hosts_list(filepath=hosts_filename)

    results = compare_hosts_list(after_list=final_list, before_list=stored_hosts, DEBUG_DATA=True)
    DEBUG_DATA = True

    if DEBUG_DATA:
        speak_to_the_team(debug_message=results['debug_message'],
                          msgtitle="Rack Migration Testing",
                          msteams_webhook_url=msteams_webhook_url)

    return

if __name__ == "__main__":
    main()
