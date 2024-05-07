#!/usr/bin/env python
from simple_net_utils import load_directory_to_dict_list
import ipdb


def main():
    stored_userdata = load_directory_to_dict_list("Fake_Employee_Data.txt")
    ipdb.set_trace()

if __name__ == "__main__":
    main()