#!/usr/bin/env python3
from sql import sqlite3, load_db, update_identity, insert_identity, insert_request
from shlex import split
import select
import io

'''
Jon Parker Brooks - 8/13/24

This program is for simply getting some quick stats
using only the most recent nginx access.log file.

Things I'm interested in:
- IP addresses visited + frequency + total visits
- top 3 Most viewed pages + top 3 IPs visiting them
- list any and every POST that happens
- total bytes sent
'''


def parse_http_request(text: str):
    keys = ('method', 'route', 'proto')
    parts = text.split(' ')
    
    if len(parts) != 3:
        parts = ('-', ) * 3

    return dict(zip(keys, parts))


def parse_log_line(text: str) -> dict:
    ip, _, _, timestamp, _, payload, status, size, _, agent = split(text.strip())
    timestamp = timestamp.lstrip('[')
    date, time = timestamp.split(':', 1)
    return {
        'ip': ip, 
        'date': date,
        'time': time,
        'size': int(size),
        'agent': agent,
        'status': int(status),
        'payload': payload,
        'request': parse_http_request(payload)
    }


def normalize_bytes(number: int) -> str:
    if number > 1000000000:
        return f'{round(number / 1000000000)} GB'
    if number > 1000000:
        return f'{round(number / 1000000)} MB'
    if number > 1000:
        return f'{round(number / 1000)} KB'


def handle_identity(db: sqlite3.Connection, identities: dict, log: dict, commit: bool = True) -> dict:
    timestamp = log['date'] + ', ' + log['time']
    ip = log['ip']
    
    if identities.get(ip):
        identities[ip]['lastseen'] = timestamp
        identities[ip]['requests'] += 1
        update_identity(db, ip, identities[ip], commit=commit)
    else:
        identities[ip] = {
            'requests': 1,
            'lastseen': timestamp,
            'created': timestamp
        }
        insert_identity(db, ip, identities[ip], commit=commit)

    return identities


def setup_logs(db: sqlite3.Connection, logfile: io.TextIOWrapper) -> tuple:

    identities, requests = {}, {}

    for log in (parse_log_line(line) for line in logfile.readlines()):
        identities = handle_identity(db, identities, log, commit=False)
        insert_request(db, log, commit=False)
    
    db.commit()

    return identities, requests


def main():

    print('opening access log...')
    logfile = open('/var/log/nginx/access.log', 'rt')
    
    print('loading database...')
    db = load_db('./db/logviewer.db', './db/schema.sql')

    print('setting up logs...')
    identities, requests = setup_logs(db, logfile)

    print('waiting on new connections...')

    rs, _, _ = select.select([logfile], [], [])

    try:
        while True:
            if logfile in rs:
                log = parse_log_line(logfile.readline())
                
                identities = handle_identity(db, identities, log)                
                ip, status = log['ip'], log['status']

                if status < 400:
                    status = f'\033[32m{status}\033[0m'
                else:
                    status = f'\033[31m{status}\033[0m'

                if log['request']['method'] == 'POST':
                    print(f'[ {status} ][ {ip.rjust(15, ' ')} ][ \033[33mPOST\033[0m ]')
                else:
                    print(f'[ {status} ][ {ip.rjust(15, ' ')} ]')

                print(f'IP Request #: \033[34m{identities[ip]['requests']}\033[0m')
                print(f'  User-Agent: {log['agent']}')
                print(f'   Timestamp: {log['date'] + ', ' + log['time']}')
                print(f'       Route: \033[36m{log['request']['route']}\033[0m')
                print('')
    except KeyboardInterrupt:
        print('goodbye')
    finally:
        logfile.close()

    
if __name__ == "__main__":
    main()