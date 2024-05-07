#!/usr/bin/env python

from simple_net_utils import load_directory_to_dict_list,load_hostnames_list
from checkpoint_functions import get_user_for_hosts
from simple_net_utils import is_valid_filename, file_exists
import argparse
#import ipdb

def load_check_user_data(hostfile:str,timeframe:str):
    stored_hosts = load_hostnames_list(filepath=hostfile)
    host_data = get_user_for_hosts(hosts=stored_hosts, timeframe=timeframe)
    return host_data

def load_user_data(dirfile:str="Fake_Employee_Data.txt"):
    user_data = load_directory_to_dict_list(dirfile)
    return user_data

def crosscheck_checkp_with_dir(hostfile:str,dirfile:str="Fake_Employee_Data.txt",timeframe:str="last-24-hours",just_users:bool=False):
    #TODO - create another function in noc_net_utils to get hostnames only
    host_data = load_check_user_data(hostfile=hostfile, timeframe=timeframe)
    user_data = load_user_data(dirfile=dirfile)
    final_data = enrich_hosts_with_user_data(host_data=host_data,user_data=user_data,just_users=just_users)
    return final_data

def print_user_data(user_data:list):
    for each_host in user_data:
        print(each_host['hostname'],each_host['username'],each_host['firstname'],each_host['surname'],each_host['email_address'],
              each_host['phone'],each_host['section_des'],each_host['department_des'],each_host['role'])
    return

def print_div_data(divlist:list[str]):
    for division in divlist:
        print(division)
    
    return

def fill_empty_user(userdict:dict):
    userdict['firstname'] = None
    userdict['surname'] = None
    userdict['email_address'] = None
    userdict['phone'] = None
    userdict['section_des'] = None
    userdict['department_des'] = None
    userdict['role'] = None
    return userdict

def enrich_hosts_with_user_data(host_data:list,user_data:list,just_users:bool=False):
    final_data=[]
    for each_host in host_data:
        for dir_row in user_data:
            found = False
            if each_host['username']:
                if each_host['username'].lower() == dir_row['username'].lower():
                    found = True
                    each_host['firstname'] = dir_row['firstname']
                    each_host['surname'] = dir_row['surname']
                    each_host['email_address'] = dir_row['email_address']
                    each_host['phone'] = dir_row['phone1']
                    each_host['section_des'] = dir_row['section_des']
                    each_host['department_des'] = dir_row['department_des']
                    each_host['role'] = dir_row['role']
                    final_data.append(each_host)          
                    break
            else:
                continue
        if found == False:
            #ipdb.set_trace()
            if not just_users:
                each_host = fill_empty_user(each_host)
                final_data.append(each_host)

    return final_data

def get_deps(userlist:list[dict]):
    deplist = []
    for userdict in userlist:
        if userdict['department_des'] != "MANAGEMENT":
            department = userdict['department_des']
        else:
            department = userdict['section_des']
        if department not in deplist:
            deplist.append(department)
    
    return deplist

def main():
    parser = argparse.ArgumentParser(description="Gather user data")
    parser.add_argument("-hf","--hosts_filename", help="Hosts file name", type=str, required=True)
    parser.add_argument("-df","--dir_filename", help="Directory file name", type=str, required=True) 
    parser.add_argument("-tf","--timeframe", help="Timeframe for checkpoint logs", type=str, required=True) # usually "last-24-hours"
    args = parser.parse_args()
    hosts_filename = args.hosts_filename
    dir_filename = args.dir_filename
    timeframe = args.timeframe

    if not is_valid_filename(hosts_filename):
        print("Error: Invalid filename format.")
        exit(1)

    if not file_exists(hosts_filename):
        print(f"Error: File '{hosts_filename}' does not exist.")
        exit(1)

    if not is_valid_filename(dir_filename):
        print("Error: Invalid filename format.")
        exit(1)

    if not file_exists(dir_filename):
        print(f"Error: File '{dir_filename}' does not exist.")
        exit(1)


    
    final_data = crosscheck_checkp_with_dir(hostfile=hosts_filename,
                                            dirfile=dir_filename,
                                            timeframe=timeframe,
                                            just_users=True)
    #ipdb.set_trace()
    print_user_data(user_data=final_data)
    deps = get_deps(final_data)
    print()
    print_div_data(deps)
    return

if __name__ == "__main__":
    main()
