#!/usr/bin/env python3

import os
import json
import datetime
from dotenv import load_dotenv
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException

load_dotenv()

USERNAME    = os.getenv("DEVICE_USERNAME")
PASSWORD    = os.getenv("DEVICE_PASSWORD")
SECRET      = os.getenv("DEVICE_SECRET")
DEVICE_TYPE = "cisco_ios"
TIMEOUT     = 15

DATE_STR    = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
OUTPUT_DIR  = os.path.join("configs", DATE_STR)

COMMANDS = [
    "show running-config",
]

def load_devices(filepath="../data/devices-prod.json"):
    with open(filepath, "r") as f:
        return json.load(f)

def connect_and_backup(device: dict) -> None:
    name = device["name"]
    host = device["host"]

    conn_params = {
        "device_type": DEVICE_TYPE,
        "host":        host,
        "username":    USERNAME,
        "password":    PASSWORD,
        "secret":      SECRET,
        "timeout":     TIMEOUT,
        "global_delay_factor": 2,
    }

    print(f"[*] Connecting: {name} ({host}) ...", end=" ", flush=True)

    try:
        with ConnectHandler(**conn_params) as net_connect:
            if SECRET:
                net_connect.enable()

            output_lines = [f"# Backup: {name}  |  {datetime.datetime.now()}\n"]

            for cmd in COMMANDS:
                output_lines.append(f"\n{'='*60}\n# {cmd}\n{'='*60}\n")
                result = net_connect.send_command(cmd, read_timeout=90)
                output_lines.append(result)

            filepath = os.path.join(OUTPUT_DIR, f"{name}_running-config.txt")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("\n".join(output_lines))

            print(f"OK {filepath}")

    except NetmikoTimeoutException:
        print(f"ERROR: Timeout")
    except NetmikoAuthenticationException:
        print(f"ERROR: Auth failed")
    except Exception as e:
        print(f"ERROR: {e}")

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    try:
        devices = load_devices()
    except FileNotFoundError:
        print("ERROR: data/devices-prod.json not found.")
        return

    print(f"\n{'='*60}")
    print(f"  SSH Config Backup: {DATE_STR}")
    print(f"  Save folder: {OUTPUT_DIR}")
    print(f"{'='*60}\n")

    for device in devices:
        connect_and_backup(device)

    print(f"\n Done! Location: {OUTPUT_DIR}/\n")

if __name__ == "__main__":
    main()