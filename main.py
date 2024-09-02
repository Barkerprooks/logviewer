#!/usr/bin/env python3

from sql import load_db, insert_request, insert_address, insert_user_agent, update_address
from shlex import split
import sys


'''
Jon Parker Brooks - 8/13/24

This program is for simply getting some quick stats
using only the most recent nginx access.log file.

Things I'm interested in:
- IP addresses visited + frequency + total visits
- top 3 Most viewed pages + top 3 IPs visiting them
- list any and every POST that happens
- total bytes sent/recv by a user

v2: 9/2/24
- find a way to use a custom log format to make my code cleaner
  - $remote_addr "$time_iso8601" "$request" $status $bytes_sent "$http_user_agent" "$request_body"
  - ip timestamp request status bytes agent & body are the only things relevant to my service for now
'''


CUSTOM_LOGFILE_PATH = sys.argv[1] if len(sys.argv) == 2 else '/var/log/nginx/website.log'


# v1 -> v2 functions

def parse_http_request(text: str) -> dict:
    
    keys = ('method', 'route', 'proto')
    parts = text.split(' ')
    
    if len(parts) != 3:
        parts = ('-', ) * 3 # if unparsable just display -

    return dict(zip(keys, parts))


def normalize_bytes(number: int) -> str:
    
    if number > 1000000000:
        return f'{round(number / 1000000000)} GB'
    if number > 1000000:
        return f'{round(number / 1000000)} MB'
    if number > 1000:
        return f'{round(number / 1000)} KB'


def parse_custom_log(line: bytes) -> dict:
    return dict(
        zip(
            ( # keys for values from line
                'ip',
                'created', # timestamp 
                'request', 
                'response', # response status (200, 404, etc) 
                'bytes', # length of bytes in request 
                'user_agent',
                'body'
            ), # values (contents of line)
            split(line.decode('utf-8', 'replace').strip())
        )
    )


def v2():

    db = load_db('./db/testing.db', './db/schema_v2.sql')
    visits = {}

    with open(CUSTOM_LOGFILE_PATH, 'rb') as file:
        for line in file.readlines():
            request = parse_custom_log(line)
            ip, timestamp, agent = request['ip'], request['created'], request['user_agent']

            if visits.get(ip):
                visits[ip] += 1
                update_address(db, ip, visits[ip], timestamp)
            else:
                visits[ip] = 1
                insert_address(db, ip, timestamp)

            insert_user_agent(db, agent, ip)
            insert_request(db, request)
        db.commit()
    db.close()


if __name__ == "__main__":
    v2()
