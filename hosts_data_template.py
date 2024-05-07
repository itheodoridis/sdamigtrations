ttp_template = """
<group name="host-data*">
mac-address: {{ mac_address }},host_ip: {{ host_ip }},host_name: {{ host_name }},vlan: {{ vlan }},port: {{ port }},switch-name: {{ switch_name }},switch-address: {{ switch_address }},switch-location: {{ switch_location }}
</group>
"""