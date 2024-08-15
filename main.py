#!/usr/bin/env python3
from shlex import split
import sql
from sql import sqlite3

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


HTTP_METHODS = [
    'GET',
    'PUT',
    'POST',
    'HEAD',
    'TRACE',
    'PATCH',
    'DELETE',
    'OPTIONS'
]


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


def update_identity(db: sqlite3.Connection, identities: dict, log: dict, commit: bool = True) -> dict:
    timestamp = log['date'] + ', ' + log['time']
    ip = log['ip']
    if identities.get(ip):
        identities[ip]['lastseen'] = timestamp
        identities[ip]['requests'] += 1
        sql.update_identity(db, ip, identities[ip], commit=commit)
    else:
        identities[ip] = {
            'requests': 1,
            'lastseen': timestamp,
            'created': timestamp
        }
        sql.insert_identity(db, ip, identities[ip], commit=commit)
    return identities


def setup_logs(db: sqlite3.Connection, path: str) -> tuple:

    identities, requests = {}, {}

    with open('access.log', 'r') as file:
        for log in (parse_log_line(line) for line in file.readlines()):
            identities = update_identity(db, identities, log, commit=False)
            sql.insert_request(db, log, commit=False)
    
    db.commit()

    return identities, requests


def main():
    print('loading database...')
    db = sql.load_db('./db/logviewer.db', './db/schema.sql')

    identities, requests = setup_logs(db, 'access.log')

    with open('access.log', 'rt') as file:
        while file.readable():
            if line := file.readline():
                log = parse_log_line(line)
                
                identities = update_identity(db, identities, log)
                
                status = log['status']
                route = log['request']['route']
                ip = log['ip']

                if status == 200:
                    print(f'{ip} just accessed {route}')
                else:
                    print(f'{ip} just tried to access {route} but got a {status} code')

                print(f'{ip} requests:', identities[ip]['requests'])

    


if __name__ == "__main__":
    main()