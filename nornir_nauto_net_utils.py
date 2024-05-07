#!/usr/bin/env python
from platform import platform
from nornir import InitNornir
from nornir.core.exceptions import NornirSubTaskError
from nornir_netmiko.tasks import netmiko_send_command, netmiko_send_config
from nornir_utils.plugins.functions import print_result
from nornir.core.inventory import ConnectionOptions
from nornir.core.filter import F
from netmiko import ConnectHandler, NetmikoAuthenticationException, NetMikoTimeoutException, NetmikoBaseException
from paramiko import AuthenticationException
from paramiko.ssh_exception import SSHException
#TODO Add timeout exception
import requests
import time
import pprint
import logging
from rich.console import Console
from rich.table import Table
from device_credentials import dev_username, dev_password
from simple_net_utils import save_the_list,print_the_list
import pymsteams
from simple_net_utils import transform_mac, inverse_transform_mac,get_hostname
from host_prefixes import prefixes,guest_prefixes
from user_loc_functions import load_user_data,get_user_for_hosts,enrich_hosts_with_user_data,print_user_data

# This is useless for now. Reducing dependencies until I try to use canonical names
#import netutils
import ipdb

#logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p',
#                    filename='get_the_macs.log', level=logging.INFO)

requests.packages.urllib3.disable_warnings()
logger = logging.getLogger('nornir')
#TODO - Maybe these need to be removed
Global_DATA_LOGGING = False
Global_DEBUG_DATA = False

def reset_connection(host):
    """Remove host from the Nornir connection table."""
    try:
        host.close_connections()
    except ValueError:
        pass

'''This function runs a show command and returns data in the form of a result object'''
def get_show_data(task,show_command:str):
    time.sleep(2)
    try:
        task.host.get_connection("netmiko", configuration=task.nornir.config)
        show_data = task.run(name="show_me_your_data",
                                    task=netmiko_send_command,
                                    command_string=show_command, 
                                    use_textfsm=True, enable=True)
        task.host.close_connection("netmiko")
    except NornirSubTaskError as e:
        # Check type of exception
        if (isinstance(e.result.exception, NetmikoAuthenticationException)) or (isinstance(e.result.exception, AuthenticationException)):
            # Remove the failed result
            task.results.pop()
            reset_connection(task.host)
            # Try again
            time.sleep(1)
            task.host.get_connection("netmiko", configuration=task.nornir.config)
            show_data = task.run(name="show_me_your_data",
                                    task=netmiko_send_command,
                                    command_string=show_command, 
                                    use_textfsm=True, enable=True)
            task.host.close_connection("netmiko")
    return(show_data)

'''This function runs a show command and returns data in the form of a result object'''
def get_show_data_multiple(task,show_commands:list[str]):
    time.sleep(2)
    command_results = {}
    try:
        task.host.get_connection("netmiko", configuration=task.nornir.config)
        for show_command in show_commands:
            show_data = task.run(name="show_me_your_data",
                                        task=netmiko_send_command,
                                        command_string=show_command, 
                                        use_textfsm=True, enable=True)
            command_results[show_command]=show_data
        task.host.close_connection("netmiko")
    except NornirSubTaskError as e:
        # Check type of exception
        if (isinstance(e.result.exception, NetmikoAuthenticationException)) or (isinstance(e.result.exception, AuthenticationException)):
            # Remove the failed result
            task.results.pop()
            reset_connection(task.host)
            # Try again
            time.sleep(1)
            task.host.get_connection("netmiko", configuration=task.nornir.config)
            for show_command in show_commands:
                show_data = task.run(name="show_me_your_data",
                                        task=netmiko_send_command,
                                        command_string=show_command, 
                                        use_textfsm=True, enable=True)
                command_results[show_command]=show_data
            task.host.close_connection("netmiko")
    return(command_results)

#TODO - The process of adding mac addresses to the list and adding to the table needs to be separated
#TODO - A separate list of dicts for host data needs to be created. Rows to be derived from it.
def add_entries(run,run_result,collect_function):
    #process results
    host_list = []
    for each_result in run_result:
        (node_name,node_address,node_location)=get_host_inv_data(run=run,each_result=each_result)
        check = print_check_node_results(run_result=run_result,each_result=each_result,node_name=node_name,node_address=node_address)
        if check == True:
            continue
        try:
            entries_table=run_result[each_result].result.result
            check_empty_list = check_empty_entries_list(entries_table)
            if check_empty_list == True:
                continue
                #TODO - we should add a continue statement if there are no macs

            for line in entries_table:
                host_dict=collect_function(line,node_name,node_address,node_location)
                if host_dict == None:
                    continue
                host_list.append(host_dict)

        except:
            print_bad_node(node_name=node_name,node_address=node_address)

    check_list = check_empty_entries_list(host_list)
    if check_list == False:
        return host_list
    else:
        return None

def add_entries_multiple(run,run_result,collect_all_function):

    #This loop itterates over hosts
    host_list=[]
    for each_result in run_result:
        #Get host data and check host results
        (node_name,node_address,node_location)=get_host_inv_data(run=run,each_result=each_result)
        #TODO - remove function call if not needed by checking the flag
        check = print_check_node_results(run_result=run_result,each_result=each_result,node_name=node_name,node_address=node_address)
        if check == True:
            continue
        try:
            '''Time to get results for this host. The following accesses data for this host'''
            node_results = run_result[each_result].result
            '''At this point this needs to get directed in a special function depending on the process. 
            For mac addresses it needs to be aware of the two commands, 
            show mac address-table and show cdp neighbors. Itterating over the keys will not work.'''
            entries_list = collect_all_function(node_results=node_results,node_name=node_name,node_address=node_address,node_location=node_location)
            if entries_list == None:
                continue

            host_list.extend(entries_list)
        except:
            print_bad_node(node_name=node_name,node_address=node_address)
        
    check_list = check_empty_entries_list(host_list)
    if check_list == False:
        return host_list
    else:
        return None

def get_host_inv_data(run,each_result):
    host_name = each_result
    host_address = run.inventory.hosts[each_result].dict()['hostname']
    host_location = run.inventory.hosts[each_result].dict()['data']['pynautobot_dictionary']['site']['name']
    return host_name,host_address,host_location

#Returns true if there is a failure in the result
def print_check_node_results(run_result,each_result,node_name,node_address):
    global Global_DATA_LOGGING
    global Global_DEBUG_DATA
    if Global_DEBUG_DATA == True:
        print(f"switch: {node_name} ip address: {node_address}")
    if run_result[each_result].failed:
        if Global_DEBUG_DATA == True:
            print(run_result[each_result].exception)
        if Global_DATA_LOGGING == True:
            logger.info(f" - Failure: {run_result[each_result].exception}")
        return True
    else:
        return False

def print_bad_node(node_name,node_address):
    global Global_DATA_LOGGING
    global Global_DEBUG_DATA
    if Global_DEBUG_DATA == True:
        print("something wrong with host", node_name)
    if Global_DATA_LOGGING == True:
        logger.info(f"- Something wrong with host {node_name} ip-address:{node_address}")
    return

# Returns true if there are no list entries
def check_empty_entries_list(entries_list):
    global Global_DEBUG_DATA
    if Global_DEBUG_DATA == True:
        print(f"Total entries: {len(entries_list)}")
    if not len(entries_list):
        if Global_DEBUG_DATA == True:
            print("no entries")
        return True
    else:
        return False

def collect_all_macs(node_results,node_name,node_address,node_location):
    mac_table_list = node_results["show mac address-table"].result
    cdp_nei_list = node_results["show cdp neighbors"].result
    final_mac_table_list = []
    for line in mac_table_list:
        host_dict=collect_mac(line,node_name,node_address,node_location)
        if host_dict == None:
            continue
        #TODO - change with use of netutils library for canonical names
        if host_dict["port"] in [cdp_nei["local_interface"].replace(" ","").replace("Gig","Gi").replace("Fas","Fa") for cdp_nei in cdp_nei_list]:
            continue
        final_mac_table_list.append(host_dict)
    check_list = check_empty_entries_list(final_mac_table_list)
    if not check_list:
        return final_mac_table_list
    else:
        return None

def collect_mac(line,switch_name,switch_address,switch_location):
    #if ((line["type"] == "STATIC") and ('CPU' not in line['destination_port'][0])):
    if ('CPU' not in line['destination_port'][0]):
        host_dict = dict()
        host_dict['mac_address'] = line['destination_address']
        host_dict['vlan'] = line['vlan']
        host_dict['port'] = line['destination_port'][0]
        host_dict['switch_name'] = switch_name
        host_dict['switch_address'] = switch_address
        host_dict['switch_location'] = switch_location
        return host_dict
    else:
        return None

def collect_arp(line,node_name,node_address,node_location):
    if (('Vlan' in line['interface'])):
        host_dict = dict()
        host_dict['mac_address'] = line['mac']
        host_dict['host_ip'] = line['address']
        host_dict['vlan'] = line['interface']
        host_dict['switch_name'] = node_name
        host_dict['switch_address'] = node_address
        host_dict['switch_location'] = node_location
        return host_dict
    else:
        return None

'''This function is not used'''
def collect_cdp_interfaces(line,node_name,node_address,node_location):
    host_dict = dict()
    host_dict['port'] = line['local_port']
    host_dict['switch_name'] = node_name
    host_dict['switch_address'] = node_address
    host_dict['location'] = node_location
    return host_dict

'''Gets the macs on a list to be saved and prints the macs on screen'''
#TODO - Change with return None for failure
def get_the_macs_addresses(nautobot_url,nautobot_token,filter_param_dict,SAVE_RESULTS=False,macs_filename:str="macs_data.txt",DEBUG_DATA=False,DATA_LOGGING=False):
    global Global_DATA_LOGGING
    global Global_DEBUG_DATA
    Global_DATA_LOGGING = DATA_LOGGING
    Global_DEBUG_DATA = DEBUG_DATA

    nautobot_ssl_verify = False
    #define inventory
    nr = initialize_inventory(nautobot_url,nautobot_token,filter_param_dict,nautobot_ssl_verify)

    if DATA_LOGGING==True:
        logger.info("\nSTART")
        logger.info("- Initiating Nornir")

    run_platform = 'cisco_ios'
    run_workers = 40
    run_task = get_show_data_multiple
    show_commands = ["show mac address-table","show cdp neighbors"]

    if DATA_LOGGING==True:
        logger.info(" - Starting Parallel SSH Tasks")
    ssh_run = nr.filter(F(platform="cisco-ios") | F(platform="cisco-ios-xe"))

    ssh_results = do_the_run_multiple(ssh_run,run_task,run_platform,run_workers,dev_username,dev_password,show_commands)
    #TODO - Separate the filtering from the run. Same process for both runs if possible

    if DATA_LOGGING==True:
        logger.info(" - Closed SSH Connections")
    
    #check for failures in ssh switches
    if (DEBUG_DATA == True) and (ssh_results.failed):
        print(f"SSH Failure exists: {ssh_results.failed}\nFailed SSH Hosts:")
        pprint.pprint(ssh_results.failed_hosts)
    if DATA_LOGGING==True:
        logger.info(f" - SSH Failure exists: {ssh_results.failed}")
        logger.info(" - Adding macs from ssh run to list")

    host_list = []
    ssh_host_list = add_entries_multiple(run=ssh_run,run_result=ssh_results,collect_all_function=collect_all_macs)

    #TODO - Create debug and logging for this
    if ssh_host_list != None:
        host_list.extend(ssh_host_list)

    telnet_run = nr.filter(platform="cisco-ios-telnet")
    run_platform = 'cisco_ios_telnet'
    run_workers = 4

    #TODO - we probably need a check for the size of the filtered list in case there are no telnet only nodes

    telnet_results = do_the_run_multiple(telnet_run,run_task,run_platform,run_workers,dev_username,dev_password,show_commands)
    if DATA_LOGGING == True:
        logger.info(" - Closed Telnet Connections")
        logger.info(f" - Telnet Failure exists: {telnet_results.failed}")
        logger.info(" - Adding macs from telnet run to list")
    
    #check for failures in telnet switches
    if (DEBUG_DATA==True) and (telnet_results.failed):
        print(f"Telnet Failure exists: {telnet_results.failed}\nFailed Telnet Hosts:")
        pprint.pprint(telnet_results.failed_hosts)

    #TODO - Create debug and logging for this
    telnet_host_list = add_entries_multiple(run=telnet_run,run_result=telnet_results,collect_all_function=collect_all_macs)
    if telnet_host_list != None:
        host_list.extend(telnet_host_list)

    #TODO - Create debug and logging for no macs
    if DATA_LOGGING == True:
        logger.info(" - All macs have been gathered.")

    #TODO - Create if to save only if there are macs to save
    if SAVE_RESULTS == True:
        if DATA_LOGGING == True:
            logger.info(" - Writing macs in file")

        save_mac_data(host_list=host_list,filename=macs_filename)

        if DATA_LOGGING == True:
            logger.info(" - File closed.\nEND")

    if DEBUG_DATA == True:
        create_mac_table(host_list)

    return(host_list)

def save_mac_data(host_list:list,filename:str):
    mac_list = create_entries_rows(host_list,create_mac_row)
    save_the_list(mac_list, filename)
    return()

#TODO - Change with return None for failure
def get_the_arps(nautobot_url,nautobot_token,filter_param_dict,SAVE_RESULTS:bool=False,arps_filename:str="arps_data.txt",DEBUG_DATA:bool=False,DATA_LOGGING:bool=False):
    #TODO - Maybe these should be removed
    global Global_DATA_LOGGING
    global Global_DEBUG_DATA
    Global_DATA_LOGGING = DATA_LOGGING
    Global_DEBUG_DATA = DEBUG_DATA

    if DATA_LOGGING==True:
        logger.info("\nSTART")
        logger.info("- Initiating Nornir")

    nautobot_ssl_verify = False
    #define inventory
    nr = initialize_inventory(nautobot_url,nautobot_token,filter_param_dict,nautobot_ssl_verify)

    ssh_run = nr.filter(F(platform="cisco-ios") | F(platform="cisco-ios-xe"))
    run_platform = 'cisco_ios'
    run_workers = 40
    run_task = get_show_data
    show_command = "show ip arp"

    if DATA_LOGGING==True:
        logger.info(" - Starting Parallel SSH Tasks")

    ssh_result = do_the_run(ssh_run,run_task,run_platform,run_workers,dev_username,dev_password,show_command)
    #TODO - Separate the filtering from the run. Same process for both runs if possible

    if DATA_LOGGING==True:
        logger.info(" - Closed SSH Connections")
    
    #check for failures in ssh switches
    if (DEBUG_DATA == True) and (ssh_result.failed):
        print(f"SSH Failure exists: {ssh_result.failed}\nFailed SSH Hosts:")
        pprint.pprint(ssh_result.failed_hosts)
    if DATA_LOGGING==True:
        logger.info(f" - SSH Failure exists: {ssh_result.failed}")
        logger.info(" - Adding entries from ssh run to list")
    #create list to store host mac entries
    #TODO - only create lists in the collection process, don't pass on this list. Return and extend

    host_list = []
    ssh_host_list = add_entries(ssh_run,ssh_result,collect_function=collect_arp)
    if ssh_host_list!=None:
        host_list.extend(ssh_host_list)
    else:
        #TODO - Add logging and debuging for it. This returns to the main program.
        return None

    #remove duplicates because of dual core switches
    final_list = []
    #append first entry directly to avoid checking for key errors
    final_list.append(host_list[0])
    #Loop over host entries to check for multiple sitings of the same mac in arp tables
    for host_entry in host_list:
        #append the entry only if that mac address is not already in the list
        if host_entry["mac_address"] not in [final_item["mac_address"] for final_item in final_list]:
            final_list.append(host_entry)

    if DATA_LOGGING == True:
        logger.info(" - All entries have been gathered.")

    if SAVE_RESULTS == True:
        if DATA_LOGGING == True:
            logger.info(" - Writing entries in file")

        save_arp_data(arp_list=final_list,filename=arps_filename)

        if DATA_LOGGING == True:
            logger.info(" - File closed.\nEND")

    if DEBUG_DATA == True:
        create_arp_table(final_list)

    return(final_list)

def save_arp_data(arp_list:list,filename:str):
    archive_arp_list = create_entries_rows(arp_list,create_arp_row)
    save_the_list(archive_arp_list, filename)
    return()

def initialize_inventory(nautobot_url,nautobot_token,filter_param_dict,nautobot_ssl_verify):
    #define inventory
    nr = InitNornir(
        inventory={
            "plugin": "NautobotInventory",
            "options": {
                "nautobot_url": nautobot_url,
                "nautobot_token": nautobot_token,
                "filter_parameters": filter_param_dict,
                "ssl_verify": nautobot_ssl_verify
            },
        },
    )
    return nr

def do_the_run(run,run_task,run_platform,run_workers,dev_username,dev_password,show_command):
    for item in run.inventory.hosts:
        run.inventory.hosts[item].platform = run_platform
        run.inventory.hosts[item].username = dev_username
        run.inventory.hosts[item].password = dev_password

    run.config.runner.options["num_workers"] = run_workers

    result = run.run(task=run_task,show_command=show_command)
    run.close_connections()
    return result

def do_the_run_multiple(run,run_task,run_platform,run_workers,dev_username,dev_password,show_commands):
    for item in run.inventory.hosts:
        run.inventory.hosts[item].platform = run_platform
        run.inventory.hosts[item].username = dev_username
        run.inventory.hosts[item].password = dev_password

    run.config.runner.options["num_workers"] = run_workers

    result_list = run.run(task=run_task,show_commands=show_commands)
    run.close_connections()
    return result_list

def enrich_node_mac_data(resolved_list:list,mac_list:list,SAVE_RESULTS:bool=False,hosts_filename:str="hosts_data.txt",DEBUG_DATA:bool=False,DATA_LOGGING:bool=False):
    #TODO - Add global variables to handle the modes? Better not so to be able to import the functions from other scripts
    node_list = []
    for each_mac in mac_list:
        for each_reshost in resolved_list:
            if each_mac['mac_address'] == each_reshost["mac_address"]:
                each_mac['host_ip'] = each_reshost["host_ip"]
                each_mac['host_name'] = each_reshost["host_name"]
                node_list.append(each_mac)
    
    if SAVE_RESULTS == True:
        if DATA_LOGGING == True:
            logger.info(" - Writing resolved entries in file")

        save_node_data(node_list=node_list,filename=hosts_filename)

        if DATA_LOGGING == True:
            logger.info(" - File closed.\nEND")

    return(node_list)

def save_node_data(node_list:list, filename:str):
    archive_node_list = create_entries_rows(node_list,create_host_row)
    save_the_list(archive_node_list, filename)
    return()

def compare_ise_host_list(before_list:list, after_list:list, DEBUG_DATA:bool=False, TEST_DATA:bool=False, GET_FW_DATA:bool=False, never_seen_before_number:int=0,
                          hosts_lost_number:int=0,hosts_mac_without_ip_or_user_number:int=0,hosts_with_user_but_no_ip_number:int=0,
                          hosts_ip_idle_number:int=0,hosts_ip_guest_number:int=0,hosts_with_mab_number:int=0,hosts_normal_number:int=0):
    debug_message = []

    #these are the lists to distribute hosts in
    never_seen_before = []
    hosts_lost = []
    hosts_mac_without_ip_or_user = []
    hosts_with_user_but_no_ip = []
    hosts_ip_idle = []
    hosts_ip_guest = []
    hosts_with_mab = []
    hosts_normal = []


    #these serve for code test scenarios
    never_seen_before_pass = False
    hosts_lost_pass = False
    hosts_mac_without_ip_or_user_pass = False
    hosts_with_user_but_no_ip_pass = False
    hosts_ip_idle_pass = False
    hosts_ip_guest_pass = False
    hosts_with_mab_pass = False
    hosts_normal_pass = False

    for before_host in before_list:
        if transform_mac(before_host["mac_address"]) not in [after_host["mac_address"] for after_host in after_list]:
            hosts_lost.append(before_host)
        
        else:
            for after_host in after_list:
                if transform_mac(before_host["mac_address"])==after_host["mac_address"]:
                    if (after_host["ip_address"] == "N/A"):
                        if (after_host["username"] == "N/A"):
                            hosts_mac_without_ip_or_user.append(before_host)
                            #print(f"hostname: {before_host['host_name']} with mac: {after_host['mac_address']} has no IP address")
                        else:
                            hosts_with_user_but_no_ip.append(after_host)
                            #print(f"hostname: {before_host['host_name']} with mac: {after_host['mac_address']} has no IP address in ISE - needs flapping")
                    elif after_host["username"] == "N/A":
                        if any(prefix in after_host["ip_address"] for prefix in prefixes):
                            hosts_ip_idle.append(before_host)
                            #print(f"hostname: {before_host['host_name']} with mac: {after_host['mac_address']} is in idle mode")
                    else:
                        if "host" in after_host["username"]:
                            hosts_ip_idle.append(after_host)
                        elif any(prefix in after_host["ip_address"] for prefix in guest_prefixes):
                            hosts_ip_guest.append(before_host)
                            #print(f"hostname: {before_host['host_name']} with mac: {after_host['mac_address']} is in guest mode")
                        elif ":" in after_host["username"]:
                            hosts_with_mab.append(after_host)
                            #ipdb.set_trace()
                        else:
                            hosts_normal.append(after_host)
                            #print(f"hostname: {before_host['host_name']} with user: {after_host['username']} is connected")
        

    # Print Debug Data to the console
    if (DEBUG_DATA):
        if len(hosts_lost) > 0:
            debug_message.append("\nThese hosts are lost:\n")
            #print("\nThese hosts are lost:")
            for each_host in hosts_lost:
                debug_message.append(str(each_host)+"\n")
                #print(each_host)
        if len(hosts_lost)==0:
            debug_message.append("\nSuccess! No losses!\n")
        if len(hosts_normal) > 0:
            debug_message.append("\nThese hosts are successfully authenticated with 802.1x:\n")
            for each_host in hosts_normal:
                debug_message.append(str(each_host)+"\n")
        if len(hosts_with_mab) > 0:
            debug_message.append("\nThese hosts are successfully authenticated with MAB:\n")
            for each_host in hosts_with_mab:
                debug_message.append(str(each_host)+"\n")
        if len(hosts_with_user_but_no_ip) > 0:
            debug_message.append("\nThese hosts are authenticated but have no IP in ISE and need flapping:\n")
            for each_host in hosts_with_user_but_no_ip:
                #(switch_name,switch_ip,switch_port)=get_switchport_by_mac_address(each_host["mac_address"])
                #debug_message.append(str(each_host)+f" at {switch_name} - {switch_ip} - {switch_port}"+"\n")
                debug_message.append(str(each_host)+"\n")
        if len(hosts_ip_idle) > 0:
            debug_message.append("\nThese hosts are authenticated in idle mode:\n")
            for each_host in hosts_ip_idle:
                debug_message.append(str(each_host)+"\n")
        if len(hosts_ip_guest) > 0:
            debug_message.append("\nThese hosts are in guest mode (previous connection data below):\n")
            for each_host in hosts_ip_guest:
                debug_message.append(str(each_host)+"\n")
        if len(hosts_mac_without_ip_or_user) > 0:
            debug_message.append("\nThese hosts are connected but did not receive an IP Address:\n")
            for each_host in hosts_mac_without_ip_or_user:
                debug_message.append(str(each_host)+"\n")

    # Test and store results
    if (TEST_DATA):
        if len(hosts_lost)==hosts_lost_number:
            hosts_lost_pass = True
    
    #TODO - I am not user whether I should do this here or in the return function. I guess the second one makes more sense.
    if (len(hosts_lost) and GET_FW_DATA):
        illegal_names = ["resolve_failed", "prn-"]
        #lost_host_data = [lost_host['host_name'] for lost_host in hosts_lost if lost_host['host_name']!='resolve_failed']
        lost_host_data = [get_hostname(lost_host['host_name']) for lost_host in hosts_lost if not any(illegal_name in lost_host['host_name'] for illegal_name in illegal_names)]

        user_data = load_user_data(dirfile="user_directory.txt")
        cpk_lost_host_data = get_user_for_hosts(hosts=lost_host_data)
        lost_data = enrich_hosts_with_user_data(host_data=cpk_lost_host_data,user_data=user_data,just_users=True)
        
        #ipdb.set_trace()
        #print("Lost users:")
        #print_user_data(user_data=lost_data)

        if (DEBUG_DATA):
            debug_message.append("These users are lost: ")
            debug_message.extend(lost_data)

    # changed to return a dict instead of a list of objects
    res_dict = dict()
    res_dict['debug_message']=debug_message
    res_dict['hosts_lost_pass']=hosts_lost_pass
    #TODO - The testing part of the code is not finished. I should created another test script for this, like with the original compare hosts scenario.

    #res_dict['lost_host_list']=[]
    #if len(hosts_lost) and GET_FW_DATA:
    #    for host in hosts_lost:
    #       res_dict['lost_host_list'].append(host['host_name'])

    return res_dict

def compare_hosts_list(before_list:list, after_list:list, DEBUG_DATA:bool=False, TEST_DATA:bool=False, GET_FW_DATA:bool=False, never_seen_before_number:int=0,
                       hosts_lost_number:int=0,hosts_moved_switch_diff_vlan_number:int=0,hosts_moved_same_vlan_number:int=0,
                       hosts_moved_different_vlan_number:int=0,hosts_moved_switch_same_vlan_number:int=0):
    debug_message = []
    
    #these are the lists to distribute hosts in
    never_seen_before = []
    hosts_lost = []
    hosts_moved_switch_diff_vlan = []
    hosts_moved_switch_same_vlan = []
    hosts_moved_same_vlan = []
    hosts_moved_different_vlan = []

    #these serve for code test scenarios
    never_seen_before_pass = False
    hosts_lost_pass = False
    hosts_moved_switch_diff_vlan_pass = False
    hosts_moved_switch_same_vlan_pass = False
    hosts_moved_same_vlan_pass = False
    hosts_moved_different_vlan_pass = False

    for before_host in before_list:
        if before_host["mac_address"] not in [after_host["mac_address"] for after_host in after_list]:
            hosts_lost.append(before_host)
        else:
            for after_host in after_list:
                if before_host["mac_address"]==after_host["mac_address"]:
                    if before_host["switch_address"]!=after_host["switch_address"]:
                        if before_host["vlan"]==after_host["vlan"]:
                            hosts_moved_switch_same_vlan.append(after_host)
                        else:
                            hosts_moved_switch_diff_vlan.append(after_host)
                    elif before_host["port"]!=after_host["port"]:
                        if before_host["vlan"]!=after_host["vlan"]:
                            hosts_moved_different_vlan.append(after_host)
                        else:
                            hosts_moved_same_vlan.append(after_host)

    for after_host in after_list:
        if after_host["mac_address"] not in [before_host["mac_address"] for before_host in before_list]:
            never_seen_before.append(after_host)
    
    # Print Debug Data to the console
    if (DEBUG_DATA):
        if len(never_seen_before) > 0:
            debug_message.append("\nThese hosts are new:\n")
            #print("\nThese hosts are new:")
            for each_host in never_seen_before:
                debug_message.append(str(each_host)+"\n")
                #print(each_host)
        if len(hosts_lost) > 0:
            debug_message.append("\nThese hosts are lost:\n")
            #print("\nThese hosts are lost:")
            for each_host in hosts_lost:
                debug_message.append(str(each_host)+"\n")
                #print(each_host)
        if len(hosts_moved_different_vlan) > 0:
            debug_message.append("\nThese hosts are on same switch, different port and different vlan so should not work without intervention:\n")
            #print("\nThese hosts are on same switch, different port and different vlan so should not work without intervention:")
            for each_host in hosts_moved_different_vlan:
                debug_message.append(str(each_host)+"\n")
                #print(each_host)
        if len(hosts_moved_same_vlan) > 0:
            debug_message.append("\nThese hosts are on same switch, different port but same vlan so should work:\n")
            #print("\nThese hosts are on same switch, different port but same vlan so should work:")
            for each_host in hosts_moved_same_vlan:
                debug_message.append(str(each_host)+"\n")
                #print(each_host)
        if len(hosts_moved_switch_same_vlan) > 0:
            debug_message.append("\nThese hosts have moved between switches, but same vlan, should work, check though:\n")
            #print("\nThese hosts have moved between switches, same vlan:")
            for each_host in hosts_moved_switch_same_vlan:
                debug_message.append(str(each_host)+"\n")
                #print(each_host)
        if len(hosts_moved_switch_diff_vlan) > 0:
            debug_message.append("\nThese hosts have moved between switches, different vlan, adapt accordingly:\n")
            #print("\nThese hosts have moved between switches, different vlan, adapt accordingly:")
            for each_host in hosts_moved_switch_diff_vlan:
                debug_message.append(str(each_host)+"\n")
                #print(each_host)
        if (len(never_seen_before)+len(hosts_lost)+len(hosts_moved_different_vlan)+len(hosts_moved_same_vlan)+len(hosts_moved_switch_diff_vlan)+len(hosts_moved_switch_same_vlan))==0:
            debug_message.append("\nSuccess! No changes!\n")

    # Test and store results
    if (TEST_DATA):
        if len(never_seen_before)==never_seen_before_number:
            never_seen_before_pass = True
        if len(hosts_lost)==hosts_lost_number:
            hosts_lost_pass = True
        if len(hosts_moved_different_vlan)==hosts_moved_different_vlan_number:
            hosts_moved_different_vlan_pass = True
        if len(hosts_moved_same_vlan)==hosts_moved_same_vlan_number:
            hosts_moved_same_vlan_pass = True
    #TODO - we can still check if the vlan is the same, this could make things ok, as long as we change descriptions on switches.
        if len(hosts_moved_switch_same_vlan)==hosts_moved_switch_same_vlan_number:
            hosts_moved_switch_same_vlan_pass = True
        if len(hosts_moved_switch_diff_vlan)==hosts_moved_switch_diff_vlan_number:
            hosts_moved_switch_diff_vlan_pass = True

    #changed to return a dict instead of a list of objects
    res_dict = dict()
    res_dict['debug_message']=debug_message
    res_dict['never_seen_before_pass']=never_seen_before_pass
    res_dict['hosts_lost_pass']=hosts_lost_pass
    res_dict['hosts_moved_switch_diff_vlan_pass']=hosts_moved_switch_diff_vlan_pass
    res_dict['hosts_moved_switch_same_vlan_pass']=hosts_moved_switch_same_vlan_pass
    res_dict['hosts_moved_same_vlan_pass']=hosts_moved_same_vlan_pass
    res_dict['hosts_moved_different_vlan_pass']=hosts_moved_different_vlan_pass

    res_dict['lost_host_list']=[]
    if len(hosts_lost) and GET_FW_DATA:
        for host in hosts_lost:
            res_dict['lost_host_list'].append(host['host_name'])

    return res_dict

    #return(debug_message,never_seen_before_pass,hosts_lost_pass,
    #       hosts_moved_switch_diff_vlan_pass,hosts_moved_switch_same_vlan_pass,
    #       hosts_moved_same_vlan_pass,hosts_moved_different_vlan_pass)

def speak_to_the_team(debug_message:list, msgtitle:str="", msteams_webhook_url:str=""):
    myTeamsMessage = pymsteams.connectorcard(msteams_webhook_url)
    myTeamsMessage.title(msgtitle)
    msgtxt = ""
    for line in debug_message:
        print(line)
        msgtxt += str(line) + "\n"
    msgtxt += "\n\n"
    myTeamsMessage.text(msgtxt)
    myTeamsMessage.send()
    return()

# function for printing lists
def printlist(datalist:list):
    for list_item in datalist:
        print(list_item)
    return()

#TODO - Create single table creation function with params for title, fields, colors
def create_mac_table(host_list:list):
    localtime = time.asctime(time.localtime(time.time()))
    table = Table(title="MAC ADDRESS REPORT \n" + localtime)
    table.add_column("Mac Address", justify="center", style="green")
    table.add_column("Vlan", justify="center",style="yellow")
    table.add_column("Port", justify="center",style="red")
    table.add_column("Switch Name", justify="center",style="purple")
    table.add_column("IP Address", justify="center",style="blue")
    table.add_column("Location", justify="center",style="cyan")

    #TODO - slightly more complicated to add the correct fields to a list with a function
    for end_host in host_list:
        table.add_row(end_host['mac_address'],
                end_host['vlan'],
                end_host['port'],
                end_host['switch_name'],
                end_host['switch_address'],
                end_host['switch_location'])

    console = Console()
    console.print(table)
    return(table)

#TODO - Create single table creation function with params for title, fields, colors
def create_arp_table(host_list:list):
    localtime = time.asctime(time.localtime(time.time()))
    table = Table(title="ARP REPORT \n" + localtime)
    table.add_column("Mac Address", justify="center", style="green")
    table.add_column("IP Address", justify="center",style="blue")
    table.add_column("Interface", justify="center",style="yellow")
    table.add_column("Switch Name", justify="center",style="purple")
    table.add_column("Switch IP Address", justify="center",style="blue")
    table.add_column("Location", justify="center",style="cyan")

    #TODO - slightly more complicated to add the correct fields to a list with a function
    for end_host in host_list:
        table.add_row(end_host['mac_address'],
                end_host['host_ip'],
                end_host['vlan'],
                end_host['switch_name'],
                end_host['switch_address'],
                end_host['switch_location'])

    console = Console()
    console.print(table)
    return(table)

def create_entries_rows(host_list:list,row_function):
    row_list = []
    for end_host in host_list:
        row_list.append(row_function(end_host))
    return(row_list)

#TODO - Create mac description, fields and colors
def create_mac_fields():
    pass

#TODO - Create arp description, fields and colors
def create_arp_fileds():
    pass

#TODO - Create single row creation function with descriptions and fields
def create_row():
    pass

def create_mac_row(end_host):
    return(f"mac-address: {end_host['mac_address']}," 
                f"vlan: {end_host['vlan']},"
                f"port: {end_host['port']}," 
                f"switch-name: {end_host['switch_name']},switch-address: {end_host['switch_address']},"
                f"switch-location: {end_host['switch_location']}\n")

def create_arp_row(end_host):
    return(f"mac-address: {end_host['mac_address']}," 
                f"ip-address: {end_host['host_ip']},"
                f"interface: {end_host['vlan']}," 
                f"switch-name: {end_host['switch_name']},switch-address: {end_host['switch_address']},"
                f"switch-location: {end_host['switch_location']}\n")

def create_host_row(end_host):
    return(f"mac-address: {end_host['mac_address']},"
                f"host_ip: {end_host['host_ip']},host_name: {end_host['host_name']},"
                f"vlan: {end_host['vlan']},"
                f"port: {end_host['port']}," 
                f"switch-name: {end_host['switch_name']},switch-address: {end_host['switch_address']},"
                f"switch-location: {end_host['switch_location']}\n")

def print_table(table):
    console = Console()
    console.print(table)
    return

def main():
    return

if __name__ == "__main__":
    main()
