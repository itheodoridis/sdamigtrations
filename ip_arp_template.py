ttp_template = """
<group name="ip-arps*">
mac-address: {{ mac_address }},ip-address: {{ host_ip }},interface: {{ port }},switch-name: {{ switch_name }},switch-address: {{ switch_ip }},switch-location: {{ switch_location }}
</group>
"""