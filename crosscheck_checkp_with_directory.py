#!/usr/bin/env python
from simple_net_utils import load_directory_to_dict_list,load_hostnames_list
from checkpoint_functions import get_user_for_hosts
#import ipdb

def main():

    #TODO - create another function in noc_net_utils to get hostnames only
    stored_hosts = load_hostnames_list(filepath="Fake_Network_Data.txt")
    host_data = get_user_for_hosts(hosts=stored_hosts, timeframe="last-24-hours")
    stored_userdata = load_directory_to_dict_list("Fake_Employee_Data.txt")
    for each_host in host_data:
        for dir_row in stored_userdata:
            not_found = True
            if each_host['username'].lower() == dir_row['username'].lower():
                each_host['firstname'] = dir_row['firstname']
                each_host['surname'] = dir_row['surname']
                each_host['email_address'] = dir_row['email_address']
                each_host['phone'] = dir_row['phone1']
                each_host['section_des'] = dir_row['section_des']
                each_host['department_des'] = dir_row['department_des']
                each_host['role'] = dir_row['role']
                not_found = False
                break
        if not_found:
            each_host['firstname'] = None
            each_host['surname'] = None
            each_host['email_address'] = None
            each_host['phone'] = None
            each_host['section_des'] = None
            each_host['department_des'] = None
            each_host['role'] = None

    #ipdb.set_trace()

    for each_host in host_data:
        print(each_host['hostname'],each_host['username'],each_host['firstname'],each_host['surname'],each_host['email_address'],
              each_host['phone'],each_host['section_des'],each_host['department_des'],each_host['role'])

    return()

if __name__ == "__main__":
    main()
