#!/usr/bin/env python3

import json
import logging
import datetime
from netmiko import ConnectHandler
from netmiko.exceptions import NetmikoTimeoutException, NetmikoAuthenticationException
import os
from dotenv import load_dotenv


LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)
log_file = os.path.join(LOG_DIR, f"acl_deploy_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

USERNAME = os.getenv("DEVICE_USERNAME")
PASSWORD = os.getenv("DEVICE_PASSWORD")
SECRET   = os.getenv("DEVICE_SECRET")

with open(os.path.join(DATA_DIR, "devices.json")) as f:
    DEVICES = json.load(f)

with open(os.path.join(DATA_DIR, "roles.json")) as f:
    ROLES = json.load(f)

with open(os.path.join(DATA_DIR, "acls.json")) as f:
    ACLS = json.load(f)

def deploy(device: dict) -> bool:
    host = device["host"]
    name = device["name"]
    role = device["role"]
    label = f"{name} ({host})"
    log.info(f"[{label}] Connecting (role: {role})...")

    conn_params = {
        "device_type": "cisco_ios",
        "host": host,
        "username": USERNAME,
        "password": PASSWORD,
        "secret": SECRET,
    }

    try:
        with ConnectHandler(**conn_params) as conn:
            conn.enable()
            log.info(f"[{label}] Entered enable mode.")

            for acl_name in ROLES[role]:
                commands = ACLS[acl_name]
                output = conn.send_config_set(commands)
                log.info(f"[{label}] Applied '{acl_name}':\n{output}")

            save_output = conn.save_config()
            log.info(f"[{label}] Config saved: {save_output.strip()}")

        log.info(f"[{label}] ✅ Done.")
        return True

    except NetmikoAuthenticationException:
        log.error(f"[{label}] ❌ Authentication failed.")
    except NetmikoTimeoutException:
        log.error(f"[{label}] ❌ Connection timed out.")
    except Exception as e:
        log.error(f"[{label}] ❌ Unexpected error: {e}")

    return False


def main():
    log.info("=" * 60)
    log.info("Starting ACL Deployment")
    log.info("=" * 60)

    results = {"success": [], "failed": []}

    for device in DEVICES:
        label = f"{device['name']} ({device['host']})"
        if deploy(device):
            results["success"].append(label)
        else:
            results["failed"].append(label)

    log.info("=" * 60)
    log.info("Deployment Summary")
    log.info("=" * 60)
    log.info(f"✅ Succeeded ({len(results['success'])}): {', '.join(results['success']) or 'None'}")
    log.info(f"❌ Failed    ({len(results['failed'])}): {', '.join(results['failed']) or 'None'}")
    log.info(f"📄 Log saved to: {log_file}")

if __name__ == "__main__":
    main()