import json
import time
import threading
import requests
import logging
import boto3
from datetime import datetime, timedelta

# Thiết lập logging: stdout và stderr
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

s3 = boto3.client('s3')
BUCKET = 'your-bucket'
CRON_FILE = 'cron_jobs.json'

def load_cron_jobs():
    try:
        obj = s3.get_object(Bucket=BUCKET, Key=CRON_FILE)
        data = json.loads(obj['Body'].read())
        logging.info(f"Loaded cron_jobs.json from S3: {data}")
        return data
    except Exception as e:
        logging.info(f"Error loading from S3: {str(e)}, returning empty list")
        return []

def save_cron_jobs(cron_jobs):
    try:
        s3.put_object(Bucket=BUCKET, Key=CRON_FILE, Body=json.dumps(cron_jobs))
        logging.info(f"Saved cron_jobs.json to S3: {cron_jobs}")
    except Exception as e:
        logging.error(f"Error saving to S3: {str(e)}")

def run_cron_job(cron):
    logging.info(f"Thread started for cron {cron['id']}: {cron['link']}")
    while True:
        # Kiểm tra trạng thái từ file S3 để cập nhật
        cron_jobs = load_cron_jobs()
        current_cron = next((c for c in cron_jobs if c['id'] == cron['id']), None)
        if not current_cron or current_cron['status'] != 'running':
            logging.info(f"Cron {cron['id']} stopped or deleted")
            break
        try:
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
            # Cập nhật cron_jobs.json
            cron_jobs = load_cron_jobs()
            for c in cron_jobs:
                if c['id'] == cron['id']:
                    c.update({'last_run': cron['last_run'], 'next_run': cron['next_run']})
            save_cron_jobs(cron_jobs)
            logging.info(f"Cron {cron['id']} ({cron['link']}): {response.status_code}")
        except Exception as e:
            logging.error(f"Cron {cron['id']} ({cron['link']}): Error - {str(e)}")
        time.sleep(cron['interval'])

def cron_manager():
    logging.info("Cron manager started")
    processed_cron_ids = set()
    while True:
        cron_jobs = load_cron_jobs()
        for cron in cron_jobs:
            if cron['status'] == 'running' and cron['id'] not in processed_cron_ids:
                logging.info(f"Starting thread for cron {cron['id']}")
                thread = threading.Thread(target=run_cron_job, args=(cron.copy(),), name=f"cron_{cron['id']}")
                thread.start()
                processed_cron_ids.add(cron['id'])
        # Xóa ID của các Cron đã bị xóa hoặc dừng
        processed_cron_ids = {cid for cid in processed_cron_ids if any(c['id'] == cid and c['status'] == 'running' for c in cron_jobs)}
        time.sleep(1)

if __name__ == "__main__":
    threading.Thread(target=cron_manager, daemon=True).start()
    while True:
        time.sleep(3600)
