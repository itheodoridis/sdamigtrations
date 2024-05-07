'''This script serves as a test for the code with test data per scenario'''
from nornir_nauto_net_utils import compare_hosts_list,speak_to_the_team
from simple_net_utils import load_hosts_list
from msteams_credentials import msteams_webhook_url
import ipdb

def main():

    never_seen_before_number=0
    hosts_lost_number=2
    hosts_moved_switch_diff_vlan_number=0
    hosts_moved_switch_same_vlan_number=1
    hosts_moved_same_vlan_number=1
    hosts_moved_different_vlan_number=1

    TEST_DATA = True
    DEBUG_DATA = True

    before_hosts = load_hosts_list(filepath="test_hosts_data_before.txt")
    after_hosts = load_hosts_list(filepath="test_hosts_data_after.txt")
    
    results=compare_hosts_list(before_hosts,after_hosts,TEST_DATA=TEST_DATA,DEBUG_DATA=DEBUG_DATA,
                               never_seen_before_number=never_seen_before_number,
                               hosts_lost_number=hosts_lost_number,
                               hosts_moved_switch_diff_vlan_number=hosts_moved_switch_diff_vlan_number,
                               hosts_moved_switch_same_vlan_number=hosts_moved_switch_same_vlan_number,
                               hosts_moved_same_vlan_number=hosts_moved_same_vlan_number,
                               hosts_moved_different_vlan_number=hosts_moved_different_vlan_number)
    
    #TODO - Refactor code to receive a dictionary instead of a list

    debug_message = results['debug_message']

    if (results['never_seen_before_pass'] and 
        results['hosts_lost_pass'] and 
        results['hosts_moved_switch_diff_vlan_pass'] and 
        results['hosts_moved_switch_same_vlan_pass'] and 
        results['hosts_moved_same_vlan_pass'] and
        results['hosts_moved_different_vlan_pass']):
        debug_message.append("\n\nAll tests passed!\n\n")
    else:
        debug_message.append("\n\nThere were test failures!\n\n")

    debug_message.append("Test for Never Seen Before: " + "Success!\n" if results['never_seen_before_pass'] else "Failed!\n")
    debug_message.append("Test for Hosts Lost: " + "Success!\n" if results['hosts_lost_pass'] else "Failed!\n")
    debug_message.append("Test for Hosts Moved Switch Different Vlan: " + "Success!\n" if results['hosts_moved_switch_diff_vlan_pass'] else "Failed!\n")
    debug_message.append("Test for Hosts Moved Switch Same Vlan: " + "Success!\n" if results['hosts_moved_switch_same_vlan_pass'] else "Failed!\n")
    debug_message.append("Test for Hosts Moved Same Vlan: " + "Success!\n" if results['hosts_moved_same_vlan_pass'] else "Failed!\n")
    debug_message.append("Test for Hosts Moved Different Vlan: " + "Success!\n" if results['hosts_moved_different_vlan_pass'] else "Failed!\n")

    if DEBUG_DATA :
        speak_to_the_team(debug_message=debug_message,
                          msgtitle="Rack Migration Testing",
                          msteams_webhook_url=msteams_webhook_url)

    return()

if __name__ == "__main__":
    main()
