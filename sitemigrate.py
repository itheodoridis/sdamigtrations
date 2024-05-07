#!/usr/bin/env python
from nornir_nauto_net_utils import get_the_macs_addresses,get_the_arps,enrich_node_mac_data
from simple_net_utils import node_resolve
from nautobot_credentials import nautobot_url, nautobot_token

def gather_tagged_switch_data(site:str, tag:str=None,
                              SAVE_RESULTS_macs:bool=False,DEBUG_DATA_macs:bool=False,DATA_LOGGING_macs:bool=False,macs_filename:str="macs_data.txt",
                              SAVE_RESULTS_arps:bool=False,DEBUG_DATA_arps:bool=False,DATA_LOGGING_arps:bool=False,arps_filename:str="arps_data.txt",
                              SAVE_RESULTS_hosts:bool=False,DEBUG_DATA_hosts:bool=False,DATA_LOGGING_hosts:bool=False,hosts_filename:str="hosts_data.txt"):
    if tag == None:
        # Create a filter to include only access switches with the tag "moved-to-new-rack" which means those that are moving to the new rack
        filter_param_dict = {"status": "active", "site" : [site], "role" : "ac-access-switch",
                    "has_primary_ip": True}
    else:
        # Create a filter to include only access switches with the tag "moved-to-new-rack" which means those that are moving to the new rack
        filter_param_dict = {"status": "active", "site" : [site], "role" : "ac-access-switch", "tag" : tag,
                    "has_primary_ip": True}

    # this calls the function to gather the mac addresses from the switches. If no addresses are gathered, it displays a message and exits.
    mac_list = get_the_macs_addresses(nautobot_url,nautobot_token,filter_param_dict,SAVE_RESULTS=SAVE_RESULTS_macs,macs_filename=macs_filename,DEBUG_DATA=DEBUG_DATA_macs,DATA_LOGGING=DATA_LOGGING_macs)
    if mac_list == None:
        print("no mac addresses were collected")
        exit(code=-1)

    # This creates a filter for the L3 switches to get the arp data. Right now the site is statically defined.
    filter_param_dict = {"status": "active", "site" : [site], "role" : "ac-distribution-switch", 
                "has_primary_ip": True}

    # This functions gets the arp data. If no arp data is collected, it displays a message and exits.
    arp_list = get_the_arps(nautobot_url,nautobot_token,filter_param_dict,SAVE_RESULTS=SAVE_RESULTS_arps,arps_filename=arps_filename,DEBUG_DATA=DEBUG_DATA_arps,DATA_LOGGING=DATA_LOGGING_arps)
    if arp_list == None:
        print("no arp entries were collected")
        exit(code=-1)
    
    resolved_list=node_resolve(arp_list)

    # This function enriches the initial host data with the additional info gathered from arp and dns. 
    # If the final list contains no data, a message is displayed and the program exits.    
    final_list = enrich_node_mac_data(resolved_list,mac_list,SAVE_RESULTS=SAVE_RESULTS_hosts,hosts_filename=hosts_filename,DEBUG_DATA=DEBUG_DATA_hosts,DATA_LOGGING=DATA_LOGGING_hosts)
    if final_list == None:
        print("no resolved entries were collected")
        exit(code=-1)

    return final_list

def macarp_filter(site:str=None,tag:str=None, role:str=None):
    filter_dict = dict()
    filter_dict["status"]="active"
    filter_dict["has_primary_ip"]=True
    if tag != None:
        filter_dict["tag"] = tag
    if site != None:
        filter_dict["site"] = site
    if role != None:
        filter_dict["role"] = role

    return filter_dict

def gather_mac_data(site:str=None, tag:str=None,role=None,
                    SAVE_RESULTS_macs:bool=False,DEBUG_DATA_macs:bool=False,DATA_LOGGING_macs:bool=False,macs_filename:str="macs_data.txt"):
    mac_filter_dict = macarp_filter(site=site,tag=tag,role=role)
    mac_list = get_the_macs_addresses(nautobot_url,nautobot_token,mac_filter_dict,SAVE_RESULTS=SAVE_RESULTS_macs,macs_filename=macs_filename,DEBUG_DATA=DEBUG_DATA_macs,DATA_LOGGING=DATA_LOGGING_macs)
    if mac_list == None:
        print("no mac addresses were collected")
        exit(code=-1)
    return mac_list

def gather_arp_data(site:str=None, tag:str=None,role=None,
                          SAVE_RESULTS_arps:bool=False,DEBUG_DATA_arps:bool=False,DATA_LOGGING_arps:bool=False,arps_filename:str="arps_data.txt"):
    arp_filter_dict = macarp_filter(site=site,tag=tag,role=role)
    arp_list = get_the_arps(nautobot_url,nautobot_token,arp_filter_dict,SAVE_RESULTS=SAVE_RESULTS_arps,arps_filename=arps_filename,DEBUG_DATA=DEBUG_DATA_arps,DATA_LOGGING=DATA_LOGGING_arps)
    if arp_list == None:
        print("no arp entries were collected")
        exit(code=-1)
    return arp_list

def resolve_and_join(mac_list=None, arp_list=None,
                     SAVE_RESULTS_hosts:bool=False,DEBUG_DATA_hosts:bool=False,DATA_LOGGING_hosts:bool=False,hosts_filename:str="hosts_data.txt"):
    resolved_list=node_resolve(arp_list)
    
    # This function enriches the initial host data with the additional info gathered from arp and dns. 
    # If the final list contains no data, a message is displayed and the program exits.    
    final_list = enrich_node_mac_data(resolved_list,mac_list,SAVE_RESULTS=SAVE_RESULTS_hosts,hosts_filename=hosts_filename,DEBUG_DATA=DEBUG_DATA_hosts,DATA_LOGGING=DATA_LOGGING_hosts)
    if final_list == None:
        print("no resolved entries were collected")
        exit(code=-1)

    return final_list

def main():

    return()

if __name__ == "__main__":
    main()
