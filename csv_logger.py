import pandas as pd

# returns the data from data.csv and adds a new row
# if the device is on battery power
# -------------------------------------------------
def insert_row(system_info, battery_info, encoded_battery_info):
    # read current data from data.csv
    data_frame = pd.read_csv("data.csv")
    
    # create a new row when new data is collected
    # (only when the system isnt charging)
    if battery_info["charging_state"] == "No":
        new_row = { 
            "Date": system_info['Sys_Date'],
            "Time": system_info['Sys_Time'],
            "Battery_Percent": battery_info["battery_percent"],
            "Time_Remaining": battery_info["time_remaining"],
            "Battery_Condition": battery_info["battery_condition"],
            "Maximum_Capacity": battery_info["maximum_capacity"],
            "Process_Count": system_info["Process_Count"],
            "CPU_Usage": system_info["CPU_Usage"],
            "Total_Memory": system_info["Total_Memory"],
            "Used_Memory": system_info["Used_Memory"],
            "Cycle_Count": battery_info["cycle_count"],
            "Charging": encoded_battery_info["charging"],
            "Low_Power_Mode": encoded_battery_info["low_power_mode"]
        }
        # adds the new row to the data.csv file
        data_frame = pd.concat([data_frame, pd.DataFrame([new_row])], ignore_index=True)
        data_frame.to_csv("data.csv", index=False)

    return data_frame
