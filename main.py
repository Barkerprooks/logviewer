#!/usr/bin/env python3
from shlex import split

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


def parse_log_line(text: str) -> dict:
    ip, _, _, timestamp, _, request, status, size, _, agent = split(text)
    timestamp = timestamp.lstrip('[')
    date, time = timestamp.split(':', 1)
    return {
        'ip': ip, 
        'date': date,
        'time': time,
        'request': request,
        'status': status,
        'size': size,
        'agent': agent
    }


def normalize_bytes(number: int) -> str:
    if number > 1000000000:
        return f'{round(number / 1000000000)} GB'
    if number > 1000000:
        return f'{round(number / 1000000)} MB'
    if number > 1000:
        return f'{round(number / 1000)} KB'


def open_log_file(path: str) -> list:
    with open(path, 'rt') as file:
        
        total_bytes = 0
        logs, days, ips = [], {}, {}

        for line in file.readlines():
        
            log = parse_log_line(line.strip())
            date, ip = log['date'], log['ip']
            total_bytes += int(log['size'])
            
            if days.get(date) is not None:
                days[date].append(log)
            else:
                days[date] = []

            if ips.get(ip) is not None:
                ips[ip].append(log)
            else:
                ips[ip] = []

            logs.append(log)
        
        return logs, days, ips, total_bytes


def ip_addresses_summary(ips):
    for ip in sorted(ips, key=lambda x: len(ips[x]), reverse=True):
        yield ip, len(ips[ip])


def main():

    print('loading log file...')

    logs, days, ips, total_bytes = open_log_file('access.log')

    for i, (ip, visits) in enumerate(ip_addresses_summary(ips)):
        if i > 20:
            break
        print(ip + '\t', visits)


if __name__ == "__main__":
    main()