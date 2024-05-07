#!/usr/bin/env python
''' This scripts contains simple functions to get data from, process and store data to nautobot'''
import pynautobot
import requests
from nautobot_credentials import nautobot_url as NAUTOBOT_URL,nautobot_token as NAUTOBOT_TOKEN
import ipdb
requests.packages.urllib3.disable_warnings()

def get_pynb():
    # create session object for pynautobot
    session = requests.Session()
    session.verify = False

    nb = pynautobot.api(url=NAUTOBOT_URL,
                      token=NAUTOBOT_TOKEN)
    nb.http_session = session
    nb.http_session.verify = False
    return nb

def get_all_devices():
    # create session object for pynautobot
    session = requests.Session()
    session.verify = False

    nb = pynautobot.api(url=NAUTOBOT_URL,
                      token=NAUTOBOT_TOKEN)
    nb.http_session = session
    nb.http_session.verify = False
    got_data = False
    while not got_data:
        try:
            nautodevs=nb.dcim.devices.all()
            got_data=True
        except requests.exceptions.Timeout:
            print("timeout occured")
        except:
            print("something went wrong")
            exit(1)
    return(nautodevs)

def compare_tool_to_nautobot(tool_devs:list, nautodevs:list):
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
    if not len(tool_devs) or not len(nautodevs):
        print("either tool device list empty or nautobot device list empty")
        exit(1)

    exists_tool = []
    exists_nauto = []
    exists_both = []

    for item in tool_devs:
        if item["serial"] in [nautodev.serial for nautodev in nautodevs]:
            exists_both.append(item)
        else:
            exists_tool.append(item)

    for item in nautodevs:
        if item.serial not in [tool_dev["serial"] for tool_dev in tool_devs]:
            dev_item = {}
            dev_item["hostname"] = item.name
            dev_item["ipaddress"] = item.primary_ip
            dev_item["code"] = item.device_type
            dev_item["serial"] = item.serial
            exists_nauto.append(dev_item)

    return (exists_tool, exists_nauto, exists_both)

def main():
    nb=get_pynb()
    ipdb.set_trace()
    return()

if __name__ == "__main__":
    main()
