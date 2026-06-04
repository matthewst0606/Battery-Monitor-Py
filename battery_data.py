
import psutil
import datetime
import platform
import subprocess


class GetBatteryData:
    def __init__(self):
        self.system_info = {}
        self.battery_dict = {}

        self.system_info = self.get_system_info()
        self.battery_dict = self.get_battery_info()


    # a dictionary containing general system info
    # ----------------------------------------------------
    def get_system_info(self):
        memory = psutil.virtual_memory()

        self.system_info['Processor_Model'] = platform.machine()
        self.system_info[ 'Sys_Date'] = datetime.datetime.now().strftime('%d/%m/%Y')
        self.system_info['Sys_Time'] = datetime.datetime.now().strftime("%H:%M:%S")
        self.system_info['CPU_Usage'] = psutil.cpu_percent()
        self.system_info['Process_Count'] = len(psutil.pids())
        self.system_info['Total_Memory'] = round(memory.total / (1024 ** 3), 2)
        self.system_info['Used_Memory'] = round(memory.used / (1024 ** 3), 2)

        return self.system_info


    def print_system_info(self):
        print(f"""
            Processor: {self.system_info['Processor_Model']}")
            Date: {self.system_info['Sys_Date']}
            Time: {self.system_info['Sys_Time']}
            Processes: {self.system_info['Process_Count']}
            CPU usage: {self.system_info['CPU_Usage']}%
            Total Memory: {self.system_info['Total_Memory']} GB
            Used Memory: {self.system_info['Used_Memory']} GB
        """)

    # gets battery info from the system and add each
    # item to a dictionary
    # ----------------------------------------------------
    def get_battery_info(self):
        # get output from command
        ne = subprocess.getoutput("powermetrics --samplers tasks --show-process-energy -n 1")
        battery = subprocess.getoutput("system_profiler SPPowerDataType")

        # add each item from the output into the dictionary
        for index in battery.splitlines():
            if ":" in index: 
                key, value = index.split(":", 1)
                key, value = key.strip(), value.strip()
                self.battery_dict[key] = value

        battery_percent =  self.battery_dict["State of Charge (%)"]
        charging_state = self.battery_dict["Charging"]
        battery_condition = self.battery_dict["Condition"]
        maximum_capacity = self.battery_dict["Maximum Capacity"].replace("%", "")
        cycle_count = self.battery_dict["Cycle Count"]
        low_power_mode = self.battery_dict["Low Power Mode"]

        # another command (previous doesnt have time remaining)
        battery_info = subprocess.getoutput("pmset -g batt")
        batteryInfo_list = battery_info.split()

        time_remaining = batteryInfo_list[9].replace(":", "")


        # wait for the system to calculate the estimated remaining time
        if time_remaining == "(no":
            raise ValueError("battery time remaining is still calculating")


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

    def print_battery_info(self):
        print(f"""
            Percent Charge: {self.battery_dict['battery_percent']}%
            Charging: {self.battery_dict['charging_state']}
            Condition: {self.battery_dict['battery_condition']}
            Maximum Capacity: {self.battery_dict['maximum_capacity']}
            Cycle Count: {self.battery_dict['cycle_count']}
            Low Power Mode: {self.battery_dict['low_power_mode']}
            Remaining Battery: {self.battery_dict['time_remaining']}\n
        """)