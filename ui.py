from flask import Flask, render_template, request, redirect
import json
import logging
from datetime import datetime, timedelta

# Thiết lập logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler('cron_log.txt'),
        logging.StreamHandler()
    ]
)

app = Flask(__name__)
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
