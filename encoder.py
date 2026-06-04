

def encode(battery_data):
    encoded_battery_data = {}

    # Y = 1, N = 0
    encoded_battery_data["low_power_mode"] = int(battery_data["low_power_mode"].lower() == "yes")
    encoded_battery_data["charging"] = int(battery_data["charging_state"].lower() == "yes")


    print(encoded_battery_data["low_power_mode"])
    print(encoded_battery_data["charging"])

    return encoded_battery_data
