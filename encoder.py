

def encode(battery_data):
    encoded_battery_data = {}

    # Yes = 1, No = 0
    encoded_battery_data["low_power_mode"] = int(battery_data["low_power_mode"].lower() == "yes")
    encoded_battery_data["charging"] = int(battery_data["charging_state"].lower() == "yes")

    return encoded_battery_data
