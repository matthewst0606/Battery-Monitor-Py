
import psutil
import datetime
import platform
import subprocess
import json


class GetBatteryData:
    def __init__(self):
        self.system_info = {}
        self.battery_dict = {}
        self.process_dict = {}
        self.powermetrics_dict = {}

        self.system_info = self.get_system_info()
        self.battery_dict = self.get_battery_info()
        self.process_dict = self.get_process_info()
        self.powermetrics_dict = self.get_powermetrics_info()


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




    def get_process_info(self):
        processes = subprocess.getoutput("""
            top -l 2 -s 1 -o power -stats pid,command,state,power |
            awk '
            /^PID[[:space:]]+COMMAND[[:space:]]+STATE[[:space:]]+POWER/ {
                seen++
                if (seen == 2) {
                    print
                    show = 1
                    next
                }
            }
            show && /^[[:space:]]*[0-9]+/ {
                print
                count++
                    if (count == 12) exit
                }'        
        """)

        process_dict = {}
        for index in processes.splitlines():
            if " " in index: 
                pid, rest = index.split(" ", 1)
                pid, rest = pid.strip(), rest.strip()

                parts = rest.rsplit(None, 2)
                state = parts[1]
                power = parts[2]


                process_dict[pid] = {
                    "state": state,
                    "power": power
                }
        return process_dict
    


    def get_powermetrics_info(self):
        powermetrics = subprocess.getoutput("" \
            "sudo powermetrics --samplers cpu_power,gpu_power,thermal,battery,tasks --show-process-energy -n 1" \
        "")

        powermetrics_dict = {
            "cpu": {},
            "gpu": {},
            "power": {},
            "processes": {}
        }
        currentSection = ""


        for index in powermetrics.splitlines():

            if "*" in index: 
                currentSection = index.strip("*")
                currentSection.strip()
                continue

            elif " " in index:
                name,rest = index.split(" ", 1)
                name,rest = name.strip(), rest.strip()
                parts = rest.rsplit(None, len(rest))




                if parts == 0: continue
                else:
                    if index.startswith("CPU"):
                        parts = index.split()
                        core = f"core {parts[1]}"
                        if core not in powermetrics_dict['cpu']:
                            powermetrics_dict['cpu'][core] = []
                        powermetrics_dict['cpu'][core].append(parts)
                            
                    elif index.startswith("GPU"):
                        parts = index.split()
                        core = f"{parts[1].rstrip(':')}"
                        if core not in powermetrics_dict['gpu']:
                            powermetrics_dict['gpu'][core] = []
                        powermetrics_dict['gpu'][core].append(parts)

                    elif index.startswith("ALL_TASKS"):
                        parts = index.split()
                        task = f"{parts[1]}"
                        if f"{task}" not in powermetrics_dict['processes']:
                            powermetrics_dict['processes'][f"{task}"] = []

                        powermetrics_dict['processes'][f"{task}"].append(parts)


                
        return powermetrics_dict