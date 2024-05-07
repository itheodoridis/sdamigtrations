#!/usr/bin/env python
import argparse
import re
from sitemigrate import gather_tagged_switch_data

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
