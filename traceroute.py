import os
from urllib import request
import numpy as np
import json
import ipaddress

ip_address_seq = []

process = os.popen("tracert 13.72.242.14")
while True:
    line = process.readline()
    if line =="":
        break
    if line.find("Tracing route") != -1:
        continue
    line = line.replace("["," ").replace("]"," ").replace("("," ").replace(")"," ").replace("-"," ")
    try:
        ip_address_seq.append(ipaddress.IPv4Address(line.split()[-1])) 
        print(ip_address_seq)
    except Exception as e:
        print(e)
        continue

print(ip_address_seq)

location_to_check = "http://ip-api.com/json/"

for i in ip_address_seq:
    out = request.urlopen(location_to_check+np.str(i))
    val =json.load(out)
    if val['status'] !='fail':
        print("{lat:",val['lat'],", lng:",val['lon'],"},")
