from flask import Flask, jsonify, request
import docker
import psycopg2
import os
import datetime
from celery import Celery
from celery.task import periodic_task

app = Flask(__name__)

# Configure Celery
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

# Initialize Celery
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

# Connect to PostgreSQL database
conn = psycopg2.connect(
    host=os.environ.get('DB_HOST', 'localhost'),
    database=os.environ.get('DB_NAME', 'uptime'),
    user=os.environ.get('DB_USER', 'postgres'),
    password=os.environ.get('DB_PASSWORD', 'password')
)

#TODO: add security
#TODO: add exceptions
@periodic_task(run_every=datetime.timedelta(minutes=5))
def ping_host(host, end_date):
    # Start a new Docker container to perform the uptime monitoring
    client = docker.from_env()
    response = client.containers.run('alpine', ['ping', '-c', '1', host], auto_remove=True)

    # Log the response code to the database
    with conn.cursor() as cursor:
        cursor.execute(f'INSERT INTO uptime_log (host, response_code) VALUES ({host}, {response.returncode})')
        conn.commit()

    if datetime.datetime.now() >= end_date:
        # Stop the task when the target date is reached
        ping_host.ignore()


#TODO: fix this as the ping host task
@periodic_task(run_every=datetime.timedelta(minutes=1440))
def run_nmap_scan(host, end_date):
    scanner = nmap.PortScanner()

    while datetime.datetime.now() < end_date:
        scanner.scan(hosts=host, arguments='-sV')
        response = scanner.all_hosts()

        if datetime.datetime.now() >= end_date:
            # Stop the task when the target date is reached
            ping_host.ignore()



@app.route('/ping/<host>', methods=['GET'])
def ping(host):
    end_date_str = request.args.get('end_date')
    end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%dT%H:%M:%S')
    ping_host.apply_async((host, end_date), countdown=300)
    return 'UPtime monitoring started'


#TODO: fix as ping
@app.route('/nmap_scan', methods=['GET'])
def nmap_scan():
    host = request.args.get('host')
    end_date = request.args.get('end_date')
    # convert end_date to datetime object
    end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
    # start the Celery task
    run_nmap_scan.apply_async(args=[host, end_date])
    return 'Nmap scan task started'


if name == '__main__':
    app.run(debug=True)