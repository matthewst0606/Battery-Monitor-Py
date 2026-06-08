import time
import numpy as np
import torch

from sklearn.preprocessing import StandardScaler
from battery_data import GetBatteryData
from encoder import encode
from csv_logger import insert_row
from csv_logger import process_row
from csv_logger import powermetrics_row

from battery_model import BatteryModel


# more potential commands to use
#-------------------------------
# top -o cpu
# sudo powermetrics --samplers tasks --show-process-energy -n 1

# sudo powermetrics --samplers cpu_power,gpu_power -n 1
# sudo powermetrics --samplers thermal -n 1

# sudo powermetrics --samplers cpu_power,gpu_power,thermal,battery,tasks --show-process-energy -n 1


# more potential predictions
#-------------------------------
# 1. Battery drain rate


# more potential features 
#-------------------------------
# 1. better automatic brightness adjustment based on current system data/usage.
# e.g. say like a user wants to get n hours out of their battery, the model can adjust
# brightness levels and other system factors to try and adjust to that request





# while loop is mostly for debugging and collecting data
while (True): 

    try:
        data = GetBatteryData()
        system_info = data.system_info
        battery_info = data.battery_dict
        process_info = data.process_dict
        
        powermetrics_info = data.powermetrics_dict

        encoded_battery_info = encode(battery_info)

        # access the dataframe
        process_df = process_row(process_info)
        powermetrics_df = powermetrics_row(powermetrics_info)

        df = insert_row(
            system_info, 
            process_info, 
            battery_info, 
            encoded_battery_info
        )


    except ValueError as error:
        print(error)

    # selecting device (M series chip) if available
    if torch.backends.mps.is_available(): device = 'mps'
    else: device = 'cpu'
    
    feature_columns = [
        "Battery_Percent",
        "Maximum_Capacity",
        "Process_Count",
        "CPU_Usage",
        "Total_Memory",
        "Used_Memory",
        "Cycle_Count",
        "Charging",
        "Low_Power_Mode",
        "Process_Power",
        "Process_State"
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


    # using the model
    # --------------------------------------------------
    b_model = BatteryModel(device) # initialize the model and optimizer
    b_model.run_model(x_train, y_train) # running the model

    # --- evaluate model results on validation data ---
    actual_y, predicted_y, val_loss = b_model.evaluate_model(device, x_val, y_val, y_scaler)


    # --- printing model results ---
    print('\n')
    for guess, actual in zip(predicted_y[:10], actual_y[:10]):
        print(f"Predicted: {int(guess.item())} | Actual: {int(actual.item())}")

    print(f"Validation Loss: {val_loss.item():.4f}%")
    time.sleep(15)
