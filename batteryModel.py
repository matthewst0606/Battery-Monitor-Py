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

# general system info (for testing)
# ----------------------------------------------------
def get_system_info():
    system_info = {}

    system_info['Processor_Model'] = platform.machine()
    system_info['Version'] = platform.mac_ver()
    system_info['OS'] = platform.system() + platform.version()
    system_info[ 'Sys_Date'] = datetime.datetime.now().strftime('%d/%m/%Y')
    system_info['Sys_Time'] = datetime.datetime.now().strftime("%H:%M:%S")
    system_info['CPU_Usage'] = psutil.cpu_percent()
    system_info['Process_Count'] = len(psutil.pids())

    memory = psutil.virtual_memory()
    system_info['Total_Memory'] = round(memory.total / (1024 ** 3), 2)
    system_info['Used_Memory'] = round(memory.used / (1024 ** 3), 2)

    print(f" {system_info['Sys_Date']}, {system_info['Sys_Time']}")
    print(f"cpu usage: {system_info['CPU_Usage']}%")
    print(f"total mem: {system_info['Total_Memory']} GB")
    print(f"used mem: {system_info['Used_Memory']} GB")
    print(f"Process_Count: {system_info['Process_Count']}")


    return system_info


# gets battery info from the system and add each
# item to a dictionary
# ----------------------------------------------------
def get_battery_info():
    # get output from command
    battery = subprocess.getoutput("system_profiler SPPowerDataType")
    battery_dict = {}

    # add each item from the output into the dictionary
    for index in battery.splitlines():
        if ":" in index: 
            key, value = index.split(":", 1)
            key, value = key.strip(), value.strip()
            battery_dict[key] = value

    battery_percent =  battery_dict["State of Charge (%)"]
    charging_state = battery_dict["Charging"]
    battery_condition = battery_dict["Condition"]
    maximum_capacity = battery_dict["Maximum Capacity"].replace("%", "")
    cycle_count = battery_dict["Cycle Count"]
    low_power_mode = battery_dict["Low Power Mode"]


    # another command (previous doesnt have time remaining)
    battery_info = subprocess.getoutput("pmset -g batt")
    batteryInfo_list = battery_info.split()

    time_remaining = batteryInfo_list[9].replace(":", "")


    # wait for the system to calculate the estimated remaining time
    if time_remaining == "(no":
        print(f"Remaining Battery: Calculating")
        while time_remaining == "(no":
            if time_remaining != "(no": 
                charging_state = batteryInfo_list[8].replace(";", "")
                break
    

    #debug print
    print(f"""
        Percent Charge: {battery_percent}%
        Charging: {charging_state}
        Condition: {battery_condition}
        Maximum Capacity: {maximum_capacity}
        Cycle Count: {cycle_count}
        Low Power Mode: {low_power_mode}
        Remaining Battery: {time_remaining}\n
    """)

    # return a dictionary
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
# -------------------------------------------------
def insert_row():
    # read current data from data.csv
    data_frame = pd.read_csv("data.csv")

    # create a new row when new data is collected
    # (only when the system isnt charging)
    if battery_data["charging_state"] == "No":
        new_row = {
            "Date": system_info['Sys_Date'],
            "Time": system_info['Sys_Time'],
            "Battery_Percent": battery_data["battery_percent"],
            "Time_Remaining": battery_data["time_remaining"],
            "Battery_Condition": battery_data["battery_condition"],
            "Maximum_Capacity": battery_data["maximum_capacity"],
            "Process_Count": system_info["Process_Count"],
            "CPU_Usage": system_info["CPU_Usage"],
            "Total_Memory": system_info["Total_Memory"],
            "Used_Memory": system_info["Used_Memory"]
        }
        # adds the new row to the data.csv file
        data_frame = pd.concat([data_frame, pd.DataFrame([new_row])], ignore_index=True)
        data_frame.to_csv("data.csv", index=False)

    return data_frame





# main
# -------------------------------------------------
system_info = get_system_info()
battery_data = get_battery_info()

#debug
for i, v in enumerate(battery_data.items()):
    print(i, v)
print("\n")


df = insert_row() # access the dataframe


# selecting device (M series chip) if available
if torch.backends.mps.is_available(): device = 'mps'
else: device = 'cpu'


feature_columns = [
    "Battery_Percent",
    "Maximum_Capacity",
    "Process_Count",
    "CPU_Usage",
    "Total_Memory",
    "Used_Memory"
]
target_column = ["Time_Remaining"]

df = df.dropna(subset=feature_columns + target_column)


# y = traning_data; x = target_data
training_data = torch.tensor(
    df[feature_columns].values,
    dtype=torch.float32
).to(device)

target_data = torch.tensor(
    df[target_column].values,
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
    nn.Linear(6, 64), # 2 refers to input size
    nn.ReLU(),
    nn.Linear(64, 32),
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



model.eval()
with torch.no_grad():
    val_prediction = model(x_val)
    val_loss = loss_fc(val_prediction, y_val)


for prediction, real_answer in zip(val_prediction, y_val):
    print(f"Predicted: {prediction.item():.2f} | Actual: {real_answer.item():.2f}")

print(f"""
      Validation Loss: {val_loss.item():.4f}
    """)