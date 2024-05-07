#!/usr/bin/env python
from nornir_nauto_net_utils import compare_ise_host_list, speak_to_the_team
from simple_net_utils import load_hosts_list,inverse_transform_mac
from retrieve_ise_data import get_macdata_from_ise
from msteams_credentials import msteams_webhook_url
from simple_net_utils import is_valid_filename, file_exists
import argparse

def main():

    parser = argparse.ArgumentParser(description="Gather ISE data")
    parser.add_argument("-hf","--hosts_filename", help="Hosts file name", type=str, required=True)
    #parser.add_argument("-gu","--get_users", help="Hosts file name", type=bool, required=True)
    args = parser.parse_args()
    hosts_filename = args.hosts_filename
    #get_users=args.get_users

    if not is_valid_filename(hosts_filename):
        print("Error: Invalid filename format.")
        exit(1)

    if not file_exists(hosts_filename):
        print(f"Error: File '{hosts_filename}' does not exist.")
        exit(1)

    stored_hosts = load_hosts_list(filepath=hosts_filename)
    (status_code,reason,hostlist) = get_macdata_from_ise()

    if status_code == 200:
        results = compare_ise_host_list(after_list=hostlist, before_list=stored_hosts, DEBUG_DATA=True, GET_FW_DATA=True)
        DEBUG_DATA = True

        if DEBUG_DATA:
            speak_to_the_team(debug_message=results['debug_message'],
                            msgtitle="Rack Migration Testing",
                            msteams_webhook_url=msteams_webhook_url)
    else:
        print(f"Error {status_code}: {reason}")

    return()

if __name__ == "__main__":
    main()
