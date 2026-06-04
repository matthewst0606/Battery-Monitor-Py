import csv
import os
import platform
import psutil
import socket
import struct 
import datetime
import subprocess
import json

import numpy as np
import pandas as pd

import torch
import torch.optim as optim
import torch.nn as nn



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
    battery = subprocess.getoutput("system_profiler SPPowerDataType")
    battery_dict = {}

    for index in battery.splitlines():
        if ":" in index: 
            key, value = index.split(":", 1)
            key, value = key.strip(), value.strip()
            battery_dict[key] = value


    battery_info = subprocess.getoutput("pmset -g batt")
    batteryInfo_list = battery_info.split()

    battery_percent =  battery_dict["State of Charge (%)"]
    charging_state = battery_dict["Charging"]
    time_remaining = batteryInfo_list[9].replace(":", "")
    battery_condition = battery_dict["Condition"]
    maximum_capacity = battery_dict["Maximum Capacity"].replace("%", "")
    cycle_count = battery_dict["Cycle Count"]
    low_power_mode = battery_dict["Low Power Mode"]

    if time_remaining == "(no":
        print(f"Remaining Battery: Calculating")
        while time_remaining == "(no":
            if time_remaining != "(no": 
                charging_state = batteryInfo_list[8].replace(";", "")
                break
    
    print(f"""
        Percent Charge: {battery_percent}%
        Charging: {charging_state}
        Condition: {battery_condition}
        Maximum Capacity: {maximum_capacity}
        Cycle Count: {cycle_count}
        Low Power Mode: {low_power_mode}
        Remaining Battery: {time_remaining}\n
    """)

    return {
        "battery_percent": int(battery_percent),
        "time_remaining": int(time_remaining),
        "maximum_capacity": int(maximum_capacity),
        "cycle_count": int(cycle_count),
        "charging_state": charging_state,
        "low_power_mode": low_power_mode,
        "battery_condition": battery_condition,
    }


# returns the data from data.csv and adds a new row
# if the device is on battery power
def insert_row():
    data_frame = pd.read_csv("data.csv")

    if battery_data["charging_state"] == "No":
        # create a new row when new data is collected
        new_row = {
            "Date": system_info['Sys_Date'],
            "Time": system_info['Sys_Time'],
            "Battery_Percent": battery_data["battery_percent"],
            "Time_Remaining": battery_data["time_remaining"],
            "Battery_Condition": battery_data["battery_condition"],
            "Maximum_Capacity": battery_data["maximum_capacity"]
        }
        # adds the new row to the data.csv file
        data_frame = pd.concat([data_frame, pd.DataFrame([new_row])], ignore_index=True)
        data_frame.to_csv("data.csv", index=False)

    # print(data_frame)
    return data_frame





system_info = get_system_info()
battery_data = get_battery_info()

df = insert_row()

# selecting device (M series chip) if available
if torch.backends.mps.is_available(): device = 'mps'
else: device = 'cpu'

# y = traning_data; x = target_data
training_data = torch.tensor(
    df[["Battery_Percent", "Maximum_Capacity"]].values,
    dtype=torch.float32
).to(device)

target_data = torch.tensor(
    df[["Time_Remaining"]].values,
    dtype=torch.float32
).to(device)

print(f"training data: {training_data.shape}")
print(f"target data: {target_data.shape}")



split = int(len(df) * 0.8)

# first 80% of the data for training
x_train = training_data[:split]
y_train = target_data[:split]

# last 20% of the data for validation
x_val = training_data[split:]
y_val = target_data[split:]

# training and validation indices
training_idx = np.arange(0, split)
validation_idx = np.arange(split, len(df))


#debug print
print(f"""
x training: {x_train.shape}
y training: {y_train.shape}

x validation: {x_val.shape}
y validation: {y_val.shape}

training indices: {training_idx.shape}
validation indices: {validation_idx.shape}
""")


# create a sequential model
torch.manual_seed(0)
model = nn.Sequential(
    nn.Linear(2, 32), # 2 refers to input size
    nn.ReLU(),
    nn.Linear(32, 16),
    nn.ReLU(),
    nn.Linear(16, 1)
).to(device)


# create an optimizer
lr = 0.001
optimizer = optim.Adam(
    model.parameters(),
    lr=lr
)

# run the model
loss_fc = nn.L1Loss()
for epoch in range(1000):
    model.train()
    optimizer.zero_grad()

    predicted_y = model(x_train)
    loss = loss_fc(predicted_y, y_train)
    loss.backward()

    optimizer.step()

    if epoch % 100 == 0: print(f"Epoch {epoch}: {loss.item():.4f}")



