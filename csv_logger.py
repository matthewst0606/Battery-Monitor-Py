import pandas as pd

# returns the data from system_info.csv and adds a new row
# if the device is on battery power
# -------------------------------------------------
def insert_row(system_info, process_info, battery_info, encoded_battery_info):
    # read current data from system_info.csv
    battery_df = pd.read_csv("data/system_info.csv")
    process_df = pd.read_csv("data/system_processes.csv")

    for pid, info in process_info.items():
        if info["state"] == "running" : info["state"] = 1
        else: info["state"] = 0


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
            "Low_Power_Mode": encoded_battery_info["low_power_mode"],
            "Process_Power": round(process_df["POWER"].sum(), 2),
            "Process_State": process_df["STATE"].sum()
        }
        # adds the new row to the system_info.csv file
        battery_df = pd.concat([battery_df, pd.DataFrame([new_row])], ignore_index=True)
        battery_df.to_csv("data/system_info.csv", index=False)

    return battery_df





def process_row(process_info):
    rows = []

    for pid, info in process_info.items():
        if pid == "PID": continue

        new_row = {
            "POWER": info["power"],
            "STATE": 1 if info["state"] == "running" else 0
        }
        rows.append(new_row)

        process_df = pd.DataFrame(rows)
        process_df.to_csv("data/system_processes.csv", index=False)

    return process_df






def powermetrics_row(powermetrics_info):
    rows = []

    for name, info in powermetrics_info['cpu'].items():
        if name.startswith("core Power"):
            new_row = {
                'core': info[0][1],
                'frequency': info[0][3],
                'active_residency': info[1][4],
                'idle_residency': info[2][4]
            }
        else:
            new_row = {
                'core': info[0][1],
                'frequency': info[0][3],
                'active_residency': info[1][4],
                'idle_residency': info[2][4]
            }
            rows.append(new_row)



        powermetrics_df = pd.DataFrame(rows)
        powermetrics_df.to_csv("data/processor_usage.csv", index=False)


    return powermetrics_df






def powermetrics_row(powermetrics_info):
    rows = []
 
    gpu_power =  powermetrics_info['gpu']['Power'][0][2]
    active_frequency =  powermetrics_info['gpu']['HW'][0][4]
    active_residency = powermetrics_info['gpu']['HW'][1][4]
    idle_residency = powermetrics_info['gpu']['idle'][0][3]

    print(powermetrics_info['gpu']['Power'])

    print(powermetrics_info['gpu']['HW'])
    print(powermetrics_info['gpu']['idle'])

    new_row = {
        "gpu_power": gpu_power,
        "active_frequency": active_frequency,
        "active_residency": active_residency,
        "idle_residency": idle_residency
    }
    rows.append(new_row)




    powermetrics_df = pd.DataFrame(rows)
    powermetrics_df.to_csv("data/gpu_usage.csv", index=False)

    return powermetrics_df


