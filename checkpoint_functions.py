from __future__ import print_function
from cpapi import APIClient, APIClientArgs
from cp_credentials import cp_username,cp_password,cp_api_server,cp_api_port
import ipdb

def get_cp_client(cp_api_server,cp_api_port):
    client_args = APIClientArgs(server=cp_api_server,port=cp_api_port)
    cp_client = APIClient(client_args)
        
    #client.debug_file = "api_calls.json"
        
    if cp_client.check_fingerprint() is False:
        print("Could not get the server's fingerprint - Check connectivity with the server.")
        exit(1)    

    return cp_client

def cp_login(cp_client):
    # login to server:
    login_res = cp_client.login(cp_username, cp_password)

    if login_res.success is False:
        print("Login failed:\n{}".format(login_res.error_message))
        exit(1)
    return

def get_logs(timeframe:str="last-24-hours"):
    cp_client = get_cp_client(cp_api_server=cp_api_server,cp_api_port=cp_api_port)
    cp_login(cp_client)
    logs=[]
    # show logs
    print("Processing. Please wait...")
    
    show_logs_res = cp_client.api_call(command = "show-logs", payload = {
        "new-query": {
            "max-logs-per-request": 100,
            "time-frame": timeframe
        }
    })
    if show_logs_res.success is False:
        print("Failed to get the list of all log objects:\n{}".format(show_logs_res.error_message))
        exit(1)
    logs=show_logs_res.data['logs']
    query_id=show_logs_res.data['query-id']
    logs_count = show_logs_res.data['logs-count']

    while (logs_count == 100) and (len(logs) < 1000):
        more_logs_res = cp_client.api_call(command = "show-logs", payload = {
            "query-id": query_id
        })
        logs.extend(more_logs_res.data['logs'])
        query_id = more_logs_res.data['query-id']
        
        #print(len(logs))
    
    return logs
    

def get_log_for_hosts(hosts:list=None,timeframe:str="last-24-hours"):
    cp_client = get_cp_client(cp_api_server=cp_api_server,cp_api_port=cp_api_port)
    cp_login(cp_client)
    logs=[]
    # show logs
    print("Processing. Please wait...")
    for hostitem in hosts:
        show_logs_res = cp_client.api_call(command = "show-logs", payload = {
            "new-query": {
                "max-logs-per-request": 1,
                "time-frame": timeframe,
                "filter": f"src:{hostitem}"
            }
        })
        if show_logs_res.success is False:
            print("Failed to get the list of all log objects:\n{}".format(show_logs_res.error_message))
            exit(1)
        hostitem_log = show_logs_res.data['logs']
        logs.extend(hostitem_log)
    
    return logs

def get_user_for_hosts(hosts:list=None, timeframe:str="last-24-hours"):
    cp_client = get_cp_client(cp_api_server=cp_api_server,cp_api_port=cp_api_port)
    cp_login(cp_client)
    host_data_list=[]
    # show logs
    print("Processing. Please wait...")
    for hostitem in hosts:
        show_logs_res = cp_client.api_call(command = "show-logs", payload = {
            "new-query": {
                "max-logs-per-request": 1,
                "time-frame": timeframe,
                "filter": f"src:{hostitem}"
            }
        })
        if show_logs_res.success is False:
            print("Failed to get the list of all log objects:\n{}".format(show_logs_res.error_message))
            exit(1)
        if 'logs' not in show_logs_res.data.keys():
            continue
        #ipdb.set_trace()

        hostitem_log = show_logs_res.data['logs']

        if len(hostitem_log)<1:
            host_data = dict()
            host_data['hostname'] = hostitem
            host_data['fullname'] = None
            host_data['username'] = None
        else:
            if 'src_user_name' in hostitem_log[0].keys():
                host_data = dict()
                host_data['hostname'] = hostitem
                #ipdb.set_trace()
                host_data['fullname'] = hostitem_log[0]['src_user_name']
                host_data['username'] = hostitem_log[0]['src_user_name'].split('(')[-1].strip(')').lower()
            else:
                #ipdb.set_trace()
                continue

        host_data_list.append(host_data)
    
    return host_data_list

def main():
    logs=get_logs()
    ipdb.set_trace()
    return

if __name__ == "__main__":
    main()