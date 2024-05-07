#!/usr/bin/env python
from simple_net_utils import load_hosts_list,load_hostnames_list
from checkpoint_functions import get_log_for_hosts,get_user_for_hosts
import ipdb

def main():

    #stored_hosts = load_hosts_list(filepath="Fake_Network_Data.txt")

    #TODO - create another function in noc_net_utils to get hostnames only
    stored_hosts = load_hostnames_list(filepath="Fake_Network_Data.txt")
    #host_logs = get_log_for_hosts(stored_hosts)
    host_data = get_user_for_hosts(hosts=stored_hosts, timeframe="last-24-hours")

    ipdb.set_trace()

    return()

if __name__ == "__main__":
    main()
