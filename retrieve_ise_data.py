import requests
from requests.auth import HTTPBasicAuth
import xml.etree.ElementTree as ET
from sdaise_credentials import ISE_HOST,ISE_USERNAME,ISE_PASSWORD
from simple_net_utils import inverse_transform_mac

def get_macdata_from_ise():
    # Define the API URLs
    active_session_url = f'https://{ISE_HOST}/admin/API/mnt/Session/AuthList/null/null'

    # Use the HTTPBasicAuth class for basic authentication
    response = requests.get(active_session_url, auth=HTTPBasicAuth(ISE_USERNAME, ISE_PASSWORD), verify=False)

    if response.status_code == 200:
        hostlist = []
        root = ET.fromstring(response.content)

        # Extract number of active sessions
        noOfActiveSession = root.get('noOfActiveSession')
        print(f"Total active sessions: {noOfActiveSession}")

        for session in root.findall('activeSession'):
            hostdata = dict()
            # Extract details for each session
            hostdata['username'] = session.find('user_name').text if session.find('user_name') is not None else "N/A"
            hostdata['mac_address'] = session.find('calling_station_id').text if session.find('calling_station_id') is not None else "N/A"
            hostdata['ip_address'] = session.find('framed_ip_address').text if session.find('framed_ip_address') is not None else "N/A"
            hostlist.append(hostdata)

    return response.status_code,response.reason,hostlist

def main():
    (status_code,reason,hostlist) = get_macdata_from_ise()
    if status_code == 200:
        for host in hostlist:
            print(f"User: {host['username']}, MAC: {inverse_transform_mac(host['mac_address'])}, IP: {host['ip_address']}")
    else:
        print(f"Error {status_code}: {reason}")
    return()

if __name__ == "__main__":
    main()
