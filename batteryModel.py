import csv
import os
import platform
import psutil
import socket
import struct 
import datetime
import subprocess



# get battery info 
# -----------------------
# pmset -g batt
# system_profiler SPPowerDataType | grep -A10 "Condition"


def get_system_info():
    system_info = {}

    system_info['Computer_Name'] = platform.node()
    system_info['Processor_Model'] = platform.machine()
    system_info['Version'] = platform.mac_ver()
    system_info['OS'] = platform.system() + platform.version()
    system_info[ 'Sys_Time'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')



    for i, v in enumerate(system_info.items()):
        print(i, v)
    print("\n")

get_system_info()


def get_battery_info():
    battery_info = subprocess.getoutput("pmset -g batt")
    batteryInfo_list = battery_info.split()

    battery_percent = batteryInfo_list[7].removesuffix(";")
    time_remaining = batteryInfo_list[9]

    print(f"""
        Percent Charge: {battery_percent} \n
        Remaining Battery: {time_remaining}\n
    """)

get_battery_info()

def get_battery_health():
    battery_health = subprocess.getoutput("system_profiler SPPowerDataType | grep -A10 \"Condition\"")
    batteryHealth_list = battery_health.split()

    battery_condition = batteryHealth_list[1]
    maximum_capacity = batteryHealth_list[4]

    print(f"""
        Battery Condition: {battery_condition} \n
        Maximum Capacity: {maximum_capacity}\n
    """)

get_battery_health()