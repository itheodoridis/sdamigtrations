#!/usr/bin/env python
import socket
import time
import os
from subprocess import Popen, DEVNULL

from ttp import ttp
from ip_arp_template import ttp_template as arp_ttp_template
from mactemplate import ttp_template as mac_ttp_template
from hosts_data_template import ttp_template as host_ttp_template

from rich.console import Console
from rich.table import Table

import itertools
#import ipdb

import csv # for load_directory_to_dict_list

import re

def load_stored_data(filepath:str, template_type:str, main_key:str):
    with open(filepath) as data_file:
        file_content = data_file.read().rstrip("\n")

    parser = ttp(data=file_content, template=template_type)
    parser.parse()


    #ipdb.set_trace()
    # Results as multiline string
    node_address_list = parser.result()[0][0][main_key]

    return(node_address_list)

def load_hostnames_list(filepath:str):
    stored_hosts = load_hosts_list(filepath=filepath)
    hostnames_list = []
    for each_host_line in stored_hosts:
        hostnames_list.append(each_host_line['host_name'])
    return hostnames_list

def load_hosts_list(filepath:str):
    return load_stored_data(filepath=filepath,template_type=host_ttp_template,main_key="host-data")

def load_iparp_list(filepath:str):
    return load_stored_data(filepath=filepath,template_type=arp_ttp_template,main_key="ip-arps")

def load_macs(filepath:str):
    return load_stored_data(filepath=filepath,template_type=mac_ttp_template,main_key="mac-addresses")

def ping(ip_list:list):
    #clear = "clear"
    #os.system(clear)
    localtime = time.asctime(time.localtime(time.time()))
    active_list = []
    inactive_list = []
    p = {}
    #with open('reader.txt', 'r') as f:
    #    filelines = f.readlines()
    for n in ip_list:
        ip = n["host_ip"]
        p[ip] = Popen(['ping', '-c', '4', '-i', '0.2', ip], stdout=DEVNULL)

    while p:
        for ip, proc in p.items():
            if proc.poll() is not None:
                del p[ip]
                if proc.returncode == 0:
                    active_list.append(ip)
                elif proc.returncode == 1:
                    inactive_list.append(ip)
                else:
                    print(f"{ip} ERROR")
                break

    print_2col_table("PING REPORT",active_list,"Active Hosts",inactive_list,"Inactive Hosts",localtime)

    return active_list,inactive_list

def print_2col_table(table_title:str,col_a:list, col_a_subject:str,col_b:list,col_b_subject:str,localtime:str):
    table = Table(title=table_title+" \n"+localtime)
    table.add_column(col_a_subject, justify="center", style="green")
    table.add_column(col_b_subject, justify="center",style="red")
    for (a,i) in itertools.zip_longest(col_a,col_b):
        table.add_row(a,i)
    console = Console()
    console.print(table)
    return()

def get_hostname(full_address):
    """Extracts and returns the hostname up to the first dot."""
    return full_address.split('.')[0]

def node_resolve(nodelist:list):
    
    not_resolved = []

    for node_data in nodelist:
        node = dict()
        node_address = node_data["host_ip"]
        #print(node_data["host_ip"])
        try:
            #TODO - I need to just add info to the nodelist, not create new lists. Either a hostname or blank or null.
            node_hostname = socket.gethostbyaddr(node_address)[0]
            #ip_address = socket.gethostbyname(printername)
            if node_hostname!="":
                node_data["host_name"] = node_hostname
            else:
                node_data["host_name"] = "unresolved"
        except Exception:
            node_data["host_name"] = "resolve_failed"
            not_resolved.append(node_address)
            continue

    #print unresolved - this prints all data, like port, switch, etc.
    #print("These ip addresses are not resolved:")
    #for unknown_ip in not_resolved:
    #    print(unknown_ip)
    if len(nodelist)!=0:
        return(nodelist)
    else:
        return None

def transform_mac(mac:str)->str:
    # Remove any '.' characters
    mac = mac.replace('.', '')

    # Insert ':' after every two characters
    mac = ':'.join([mac[i:i+2] for i in range(0, len(mac), 2)])

    # Convert to uppercase
    mac = mac.upper()

    return mac

def inverse_transform_mac(mac:str)->str:
    # Remove any ':' characters
    mac = mac.replace(':', '')

    # Insert '.' after every four characters
    mac = '.'.join([mac[i:i+4] for i in range(0, len(mac), 4)])

    # Convert to lowercase
    mac = mac.lower()

    return mac

def save_the_list(entries_list:list, filepath:str):
    with open(filepath, 'w') as writer:
        for line in entries_list:
            writer.write(line)
    return()

#TODO - When the process of adding arp entries to arp list and adding to the table are separated, this function will print the table.
def print_the_list(arp_list:list):
    pass
    return()

def load_directory_to_dict_list(file_path:str):
    """
    Load CSV data into a list of dictionaries, extracting and processing user data.
    Each dictionary in the list corresponds to a row in the CSV, with keys for each column.
    Additionally, extract the username from the email address and add it to the dictionary.

    :param file_path: Path to the CSV file.
    :return: List of dictionaries with user data.
    """
    data_list = []

    with open(file_path, mode='r', encoding='utf-8') as file:
        # Define the field names based on the provided sample and order
        field_names = ['employee_id', 'surname', 'firstname', 'section_id', 'role', 'department_id', 
                       'employee_rank', 'phone1', 'phone2', 'email_address', 'number', 'section_id_2', 
                       'section_des', 'department_id_2', 'department_des']

        reader = csv.DictReader(file, fieldnames=field_names, delimiter=';')
        next(reader)  # Skip header row
        
        for row in reader:
            # Extract username from email address
            username = row['email_address'].split('@')[0].lower()
            row['username'] = username
            data_list.append(row)
    
    return data_list


def is_valid_filename(filename):
    if not re.match(r'^[\w\-\.]+$', filename):
        return False
    return True

def file_exists(filename):
    return os.path.exists(filename)


# Sample usage (replace 'path_to_your_file.csv' with the actual file path)
# file_path = 'path_to_your_file.csv'
# user_data = load_csv_to_dict(file_path)
# print(user_data[:2])  # Print first two rows to verify

# This script assumes the structure of the CSV file matches the sample provided.
# You'll need to replace 'path_to_your_file.csv' with the actual path to your CSV file when using this function.

def main():
    return()

if __name__ == "__main__":
    main()
