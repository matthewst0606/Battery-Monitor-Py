import platform
import psutil
import datetime
import subprocess
import sys
import time

import numpy as np
import pandas as pd

import torch
import torch.optim as optim
import torch.nn as nn

from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

# a dictionary containing general system info
# ----------------------------------------------------
def get_system_info():
    system_info = {}

    system_info['Processor_Model'] = platform.machine()
    system_info[ 'Sys_Date'] = datetime.datetime.now().strftime('%d/%m/%Y')
    system_info['Sys_Time'] = datetime.datetime.now().strftime("%H:%M:%S")
    system_info['CPU_Usage'] = psutil.cpu_percent()
    system_info['Process_Count'] = len(psutil.pids())

    memory = psutil.virtual_memory()
    system_info['Total_Memory'] = round(memory.total / (1024 ** 3), 2)
    system_info['Used_Memory'] = round(memory.used / (1024 ** 3), 2)

    return system_info


def print_system_info():
    print(f"""
           Processor: {system_info['Processor_Model']}")
                Date: {system_info['Sys_Date']}
                Time: {system_info['Sys_Time']}

           Processes: {system_info['Process_Count']}
           CPU usage: {system_info['CPU_Usage']}%
        Total Memory: {system_info['Total_Memory']} GB
         Used Memory: {system_info['Used_Memory']} GB
    """)

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


def print_battery_info():
    print(f"""
           Percent Charge: {battery_data['battery_percent']}%
                 Charging: {battery_data['charging_state']}
                Condition: {battery_data['battery_condition']}
         Maximum Capacity: {battery_data['maximum_capacity']}
              Cycle Count: {battery_data['cycle_count']}
           Low Power Mode: {battery_data['low_power_mode']}
        Remaining Battery: {battery_data['time_remaining']}\n
    """)


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



while (True):
    # main
    # -------------------------------------------------
    system_info = get_system_info()
    battery_data = get_battery_info()
    df = insert_row() # access the dataframe

    print_system_info()
    print_battery_info()


    # selecting device (M series chip) if available
    # if torch.backends.mps.is_available(): device = 'mps'
    # else: device = 'cpu'

    device = 'cpu'
    
    feature_columns = [
        "Battery_Percent",
        "Maximum_Capacity",
        "Process_Count",
        "CPU_Usage",
        "Total_Memory",
        "Used_Memory"
    ]
    target_column = ["Time_Remaining"]

    # drop each row that is missing data from the 
    # feature columns
    df = df.dropna(subset=feature_columns + target_column)

    # initialize scalers
    x_scaler = StandardScaler()
    y_scaler = StandardScaler()

    x_scaled = x_scaler.fit_transform(df[feature_columns].values)
    y_scaled = y_scaler.fit_transform(df[target_column].values)


    # traning_data = x; target_data = y
    training_data = torch.tensor(
        x_scaled,
        dtype=torch.float32
    ).to(device)

    target_data = torch.tensor(
        y_scaled,
        dtype=torch.float32
    ).to(device)


    # for a given x (training_data), 
    # the model tries to predict y (target_data)
    # --------------------------------------------------
    all_idx = np.arange(len(df))

    np.random.shuffle(all_idx)


    split = int(len(df) * 0.8)
    # # training and validation indices 
    training_idx = all_idx[0:split]
    validation_idx = all_idx[split:len(df)]

    # first 80% of the data for training
    x_train = training_data[training_idx]
    y_train = target_data[training_idx]

    # last 20% of the data for validation 
    x_val = training_data[validation_idx]
    y_val = target_data[validation_idx]



    # --- debug print ---
    print(f"""
        training indices: {training_idx.shape}
        validation indices: {validation_idx.shape}
    """)





    # --- create a sequential model ---
    torch.manual_seed(0)
    model = nn.Sequential(
        nn.Linear(6, 128), # 6 refers to input size
        nn.ReLU(),
        nn.Linear(128, 64),
        nn.ReLU(),
        nn.Linear(64, 32),
        nn.ReLU(),
        nn.Linear(32, 1),
    ).to(device)

    # --- create an optimizer ---
    lr = 0.001
    optimizer = optim.Adam(
        model.parameters(),
        lr=lr
    )

    # --- running the model ---
    loss_fc = nn.L1Loss()
    for epoch in range(2000): 
        model.train()
        optimizer.zero_grad()

        predicted_y = model(x_train)
        loss = loss_fc(predicted_y, y_train)

        loss.backward()
        optimizer.step()

        if epoch % 200 == 0: 
            print(f"Epoch {epoch}: {loss.item():.4f}")




    # --- evaluate model results on validation data ---
    model.eval()
    with torch.no_grad():
        # calculate validation loss
        x_prediction = model(x_val)
        val_loss = loss_fc(x_prediction, y_val)

        # get actual values from the scaled values
        scaled_predictions = torch.as_tensor(x_val).float().to(device)
        predictions = model(scaled_predictions).detach().cpu().numpy()

        actual_y = y_scaler.inverse_transform(y_val)
        predicted_y = y_scaler.inverse_transform(predictions)


    # --- printing model results ---
    print('\n')
    for guess, actual in zip(predicted_y[:10], actual_y[:10]):
        print(f"Predicted: {int(guess.item())} | Actual: {int(actual.item())}")

    print(f"Validation Loss: {val_loss.item():.4f}%")
    time.sleep(15)
