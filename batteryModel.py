import csv
import os
import platform
import psutil
import socket
import struct 
import datetime
import subprocess

import numpy as np
import pandas as pd

import torch
import torch.optim as optim
import torch.nn as nn



# get battery info 
# -----------------------
# pmset -g batt
# system_profiler SPPowerDataType | grep -A10 "Condition"



def get_system_info():
    system_info = {}

    system_info['Processor_Model'] = platform.machine()
    system_info['Version'] = platform.mac_ver()
    system_info['OS'] = platform.system() + platform.version()
    system_info[ 'Sys_Date'] = datetime.datetime.now().strftime('%d/%m/%Y')
    system_info['Sys_Time'] = datetime.datetime.now().strftime("%H:%M:%S")

    for i, v in enumerate(system_info.items()):
        print(i, v)
    print("\n")

    return system_info

def get_battery_info():
    # get output from command and split it
    # into a list
    battery_info = subprocess.getoutput("pmset -g batt")
    batteryInfo_list = battery_info.split()

    battery_percent = batteryInfo_list[7].removesuffix(";")
    time_remaining = batteryInfo_list[9]

    print(f"Percent Charge: {battery_percent} \n")

    if time_remaining == "(no":
        print(f"Remaining Battery: Calculating\n")
        while time_remaining == "(no":
            if time_remaining !="(no)":
                break
    
    print(f"Remaining Battery: {time_remaining}\n")
    return battery_percent, time_remaining


def get_battery_health():
    battery_health = subprocess.getoutput("system_profiler SPPowerDataType | grep -A10 \"Condition\"")
    batteryHealth_list = battery_health.split()

    battery_condition = batteryHealth_list[1]
    maximum_capacity = batteryHealth_list[4]

    print(f"Battery Condition: {battery_condition}")
    print(f"Maximum Capacity: {maximum_capacity}")

    return battery_condition, maximum_capacity


system_info = get_system_info()
battery_percent, time_remaining = get_battery_info()
battery_condition, maximum_capacity = get_battery_health()



np.random.seed(0)

data_frame = pd.read_csv("data.csv")

# create a new row when new data is collected
new_row = {
    "Date": system_info['Sys_Date'],
    "Time": system_info['Sys_Time'],
    "Battery_Percent": battery_percent,
    "Time_Remaining": time_remaining,
    "Battery_Condition": battery_condition,
    "Maximum_Capacity": maximum_capacity
}
data_frame = pd.concat([data_frame, pd.DataFrame([new_row])], ignore_index=True)
data_frame.to_csv("data.csv", index=False)
print(data_frame)

training_data = [data_frame]
target_data = [[time_remaining]]


N = len(data_frame)
split_training_data = data_frame[:int(N * 0.8)]
split_target_data = data_frame[:int(N * 0.8)]










