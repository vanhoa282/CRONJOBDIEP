from flask import Flask, render_template, request, redirect
import json
import boto3
import logging
from datetime import datetime, timedelta

# Thiết lập logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[logging.StreamHandler()]
)

app = Flask(__name__)
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

@app.route('/')
def index():
    cron_jobs = load_cron_jobs()
    running = [cron for cron in cron_jobs if cron['status'] == 'running']
    stopped = [cron for cron in cron_jobs if cron['status'] == 'stopped']
    return render_template('index.html', cron_jobs=cron_jobs, running=running, stopped=stopped)

@app.route('/add', methods=['POST'])
def add_cron():
    cron_jobs = load_cron_jobs()
    new_id = max([cron['id'] for cron in cron_jobs], default=0) + 1
    new_cron = {
        'id': new_id,
        'link': request.form['link'],
        'interval': int(request.form['interval']),
        'method': request.form['method'],
        'status': 'running',
        'last_run': None,
        'next_run': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    cron_jobs.append(new_cron)
    save_cron_jobs(cron_jobs)
    return redirect('/')

@app.route('/restart/<int:cron_id>')
def restart_cron(cron_id):
    cron_jobs = load_cron_jobs()
    for cron in cron_jobs:
        if cron['id'] == cron_id and cron['status'] == 'stopped':
            cron['status'] = 'running'
            cron['next_run'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    save_cron_jobs(cron_jobs)
    return redirect('/')

@app.route('/delete/<int:cron_id>')
def delete_cron(cron_id):
    cron_jobs = load_cron_jobs()
    cron_jobs = [cron for cron in cron_jobs if cron['id'] != cron_id]
    save_cron_jobs(cron_jobs)
    return redirect('/')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
