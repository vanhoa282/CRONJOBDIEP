import json
import time
import threading
import requests
import logging
from datetime import datetime, timedelta

# Thiết lập logging
logging.basicConfig(filename='cron_log.txt', level=logging.INFO, format='%(asctime)s - %(message)s')

CRON_FILE = 'cron_jobs.json'

def load_cron_jobs():
    try:
        with open(CRON_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_cron_jobs(cron_jobs):
    with open(CRON_FILE, 'w') as f:
        json.dump(cron_jobs, f, indent=2)

def run_cron_job(cron):
    while cron['status'] == 'running':
        try:
            # Gọi URL
            if cron['method'].upper() == 'GET':
                response = requests.get(cron['link'])
            else:
                response = requests.post(cron['link'])
            
            # Cập nhật thời gian
            cron['last_run'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cron['next_run'] = (datetime.now() + timedelta(seconds=cron['interval'])).strftime('%Y-%m-%d %H:%M:%S')
            save_cron_jobs(load_cron_jobs())  # Cập nhật file JSON
            
            # Ghi log
            logging.info(f"Cron {cron['id']} ({cron['link']}): {response.status_code}")
        except Exception as e:
            logging.error(f"Cron {cron['id']} ({cron['link']}): Error - {str(e)}")
        
        # Chờ đến lần chạy tiếp theo
        time.sleep(cron['interval'])

def cron_manager():
    while True:
        cron_jobs = load_cron_jobs()
        for cron in cron_jobs:
            if cron['status'] == 'running' and not any(t.name == f"cron_{cron['id']}" for t in threading.enumerate()):
                # Chạy Cron Job trong thread riêng
                thread = threading.Thread(target=run_cron_job, args=(cron,), name=f"cron_{cron['id']}")
                thread.start()
        time.sleep(1)  # Kiểm tra mỗi giây

if __name__ == "__main__":
    threading.Thread(target=cron_manager, daemon=True).start()
    # Giữ chương trình chạy
    while True:
        time.sleep(3600)
