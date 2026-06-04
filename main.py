import time
import numpy as np
import torch

from sklearn.preprocessing import StandardScaler
from battery_data import GetBatteryData
from encoder import encode
from csv_logger import insert_row
from battery_model import BatteryModel


# more potential commands to use
#-------------------------------
# top -o cpu
# sudo powermetrics --samplers tasks --show-process-energy -n 1


# while loop is mostly for debugging and collecting data
while (True): 

    try:
        data = GetBatteryData()
        system_info = data.system_info
        battery_info = data.battery_dict

        encoded_battery_info = encode(battery_info)
        
        # access the dataframe
        df = insert_row(
            system_info, 
            battery_info, 
            encoded_battery_info
        )

        data.print_system_info()
        data.print_battery_info()
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
        "Low_Power_Mode"
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
    time.sleep(30)
