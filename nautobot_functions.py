#!/usr/bin/env python
''' This scripts contains simple functions to get data from, process and store data to nautobot'''
import pynautobot
import requests
from nautobot_credentials import nautobot_url,nautobot_token
import ipdb

requests.packages.urllib3.disable_warnings()

def pynauto_get_api():
    # create session object for pynautobot
    session = requests.Session()
    session.verify = False

    # It's possible that the verify parameter is not needed, the session.verify should be enough, it was before.
    # Consider removing it again.
    # This is added due to https://github.com/nautobot/nornir-nautobot/issues/134
    nb = pynautobot.api(url=nautobot_url,
                      token=nautobot_token,
                      verify=False)
    nb.http_session = session
    nb.http_session.verify = False
    return nb

def pynauto_get_all_devices(nb):

    got_data = False
    while not got_data:
        try:
            nauto_devs=nb.dcim.devices.all()
            got_data=True
        except requests.exceptions.Timeout:
            print("timeout occured")
        except:
            print("something went wrong")
            exit(1)
    return(nauto_devs)

def pynauto_get_all_sites(nb):
    sites =nb.dcim.sites.all()
    return sites

# TODO - I need to be able to filter sites
def pynauto_get_all_sites_by_tag(nb,tag):
    pass

# TODO - this should be turned into a central point of reference for items in general and then certain functions would be called depending on type
def pynauto_compare_devices_tool_to_nautobot(tool_devs:list, nauto_devs:list):
    ''' 
    The tool_devs list is a list of dictionaries.
    The tool to compare with nautobot must define the following keys per device dict:
    - hostname (text field for device name)
    - ipaddress (main ipv4 address used to connect to device)
    - code (meaning vendor platform or model)
    - serial (meaning serial number)
    Any necessary processing to adapt the data must be done prior to calling this function and 
    passing the list as argument.
    '''
    if not len(tool_devs) or not len(nauto_devs):
        print("either tool device list empty or nautobot device list empty")
        exit(1)

    exists_tool = []
    exists_nauto = []
    exists_both = []

    for item in tool_devs:
        if item["serial"] in [nautodev.serial for nautodev in nauto_devs]:
            exists_both.append(item)
        else:
            exists_tool.append(item)

    for item in nauto_devs:
        if item.serial not in [tool_dev["serial"] for tool_dev in tool_devs]:
            dev_item = {}
            dev_item["hostname"] = item.name
            dev_item["ipaddress"] = item.primary_ip
            dev_item["code"] = item.device_type
            dev_item["serial"] = item.serial
            exists_nauto.append(dev_item)

    return (exists_tool, exists_nauto, exists_both)

def main():
    pass
    #ipdb.set_trace()
    return()

if __name__ == "__main__":
    main()
