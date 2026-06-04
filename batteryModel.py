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

    battery_percent = batteryInfo_list[7].replace("%;", "")
    time_remaining = batteryInfo_list[9].replace(":", "")

    print(f"Percent Charge: {battery_percent}%")

    if time_remaining == "(no":
        print(f"Remaining Battery: Calculating")
        while time_remaining == "(no":
            if time_remaining !="(no)": break
    
    print(f"Remaining Battery: {time_remaining}\n")
    return int(battery_percent), int(time_remaining)


def get_battery_health():
    battery_health = subprocess.getoutput("system_profiler SPPowerDataType | grep -A10 \"Condition\"")
    batteryHealth_list = battery_health.split()

    battery_condition = batteryHealth_list[1]
    maximum_capacity = batteryHealth_list[4].replace("%", "")


    print(f"Battery Condition: {battery_condition}")
    print(f"Maximum Capacity: {maximum_capacity}%\n")

    return battery_condition, int(maximum_capacity)

def insert_row():
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

    # adds the new row to the data.csv file
    data_frame = pd.concat([data_frame, pd.DataFrame([new_row])], ignore_index=True)
    data_frame.to_csv("data.csv", index=False)

    print(data_frame)
    return data_frame










system_info = get_system_info()
battery_percent, time_remaining = get_battery_info()
battery_condition, maximum_capacity = get_battery_health()



df = insert_row()

# selecting device (M series chip) if available
if torch.backends.mps.is_available(): device = 'mps'
else: device = 'cpu'

# y = traning_data; x = target_data
training_data = torch.tensor(
    df[["Battery_Percent", "Maximum_Capacity"]].values,
    dtype=torch.float32
).to(device)
print(f"training data: {training_data.shape}")

target_data = torch.tensor(
    df[["Time_Remaining"]].values,
    dtype=torch.float32
).to(device)

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



