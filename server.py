import json
import time
import threading
import requests
import logging
from datetime import datetime, timedelta

# Thiết lập logging: ghi vào cron_log.txt và stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('cron_log.txt'),
        logging.StreamHandler()  # Ghi log ra stdout để xem trong Koyeb
    ]
)

CRON_FILE = 'cron_jobs.json'

def load_cron_jobs():
    try:
        with open(CRON_FILE, 'r') as f:
            data = json.load(f)
            logging.info(f"Loaded cron_jobs.json: {data}")
            return data
    except FileNotFoundError:
        logging.info("cron_jobs.json not found, returning empty list")
        return []
    except Exception as e:
        logging.error(f"Error loading cron_jobs.json: {str(e)}")
        return []

def save_cron_jobs(cron_jobs):
    try:
        with open(CRON_FILE, 'w') as f:
            json.dump(cron_jobs, f, indent=2)
        logging.info(f"Saved cron_jobs.json: {cron_jobs}")
    except Exception as e:
        logging.error(f"Error saving cron_jobs.json: {str(e)}")

def run_cron_job(cron):
    while cron['status'] == 'running':
        try:
            # Kiểm tra URL hợp lệ
            if not cron['link'].startswith(('http://', 'https://')):
                logging.error(f"Cron {cron['id']} ({cron['link']}): Invalid URL")
                break
            logging.info(f"Calling {cron['link']} ({cron['method']})")
            if cron['method'].upper() == 'GET':
                response = requests.get(cron['link'], timeout=10)
            else:
                response = requests.post(cron['link'], timeout=10)
            cron['last_run'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cron['next_run'] = (datetime.now() + timedelta(seconds=cron['interval'])).strftime('%Y-%m-%d %H:%M:%S')
            save_cron_jobs(load_cron_jobs())
            logging.info(f"Cron {cron['id']} ({cron['link']}): {response.status_code}")
        except Exception as e:
            logging.error(f"Cron {cron['id']} ({cron['link']}): Error - {str(e)}")
        time.sleep(cron['interval'])

def cron_manager():
    logging.info("Cron manager started")
    while True:
        cron_jobs = load_cron_jobs()
        for cron in cron_jobs:
            if cron['status'] == 'running' and not any(t.name == f"cron_{cron['id']}" for t in threading.enumerate()):
                logging.info(f"Starting thread for cron {cron['id']}")
                thread = threading.Thread(target=run_cron_job, args=(cron,), name=f"cron_{cron['id']}")
                thread.start()
        time.sleep(1)

if __name__ == "__main__":
    threading.Thread(target=cron_manager, daemon=True).start()
    while True:
        time.sleep(3600)
