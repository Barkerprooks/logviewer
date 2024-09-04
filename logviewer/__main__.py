from logviewer.sql import initialize_db, query_db, insert_db
from logviewer.cli import Raw, NonBlocking
from logviewer.log import parse_log
from argparse import ArgumentParser
from os import get_terminal_size
from time import sleep
from datetime import datetime

import sys


argument_parser = ArgumentParser()
argument_parser.add_argument('-db', '--database', type=str, default='./db/logviewer.db')
argument_parser.add_argument('-s', '--schema', type=str, default='./db/schema.sql')
argument_parser.add_argument('-l', '--log', type=str, default='/var/log/nginx/website.log')

args = argument_parser.parse_args()


def handle_input(key: str, selected: int, request_list_length: int) -> int:
    if key == 'w' and selected > 1:
        return selected - 1
    elif key == 's' and selected < request_list_length - 1:
        return selected + 1
    elif key == 'q':
        return -1
    return selected

def build_output(selected, request_list, request_list_length, w, h):
    
    for y in range(h):
        if y == 0:
            print(('#' * (w - len(args.log) - 7)), args.log, end=' #####', flush=True)
        elif y < request_list_length:
            try:
                ip, created, request, response, length, user_agent, body = request_list[y - 1]
                method, route, protocol = request.split(' ')
                timestamp = datetime.fromisoformat(created).strftime('%m/%d/%y %H:%M:%S %p')
                line = f'{method.ljust(8 if selected == y else 10, ' ')} {response} - {ip.rjust(15, ' ')}'
                if len(line + ' ' + route) < w:
                    line += ' ' + route
                if selected == y:
                    line = '> ' + line
                print(line, end=' ' * (w - len(line)), flush=True)
            except IndexError:
                print('-', end=' ' * (w - 1), flush=True)
        elif y == h - 1:
            summary_line = f'##### total requests: {len(requests)} ##### q=quit,w=up,s=down '
            print(summary_line, end='#' * (w - len(summary_line)), flush=True)
        else:
            print(' ' * w, end='', flush=True)
        print(f'\33[{w}D\33[1B', end='', flush=True)
    print(f'\33[{h}A', end='', flush=True)


log = initialize_db(args.database, args.schema, args.log)
requests = list(query_db(args.database, 'last_n_hours', hours=12))
selected = 1

print('\33[?25l', end='')


with Raw(sys.stdin):
    with NonBlocking(sys.stdin):
        try:
            while 1: # forever (until ctrl+c)
                w, h = get_terminal_size() # make sure we always draw to the correct size screen

                # check if file has new things to read
                if line := log.readline():
                    request = parse_log(line)
                    insert_db(args.database, request)
                    requests.insert(0, request.values())

                request_list_length = h // 2
                request_list = requests[:request_list_length]

                try:
                    if key := sys.stdin.read(1):
                        selected = handle_input(key, selected, request_list_length)
                except IOError:
                    print('stdin not ready')
                
                build_output(selected, request_list, request_list_length, w, h)

                if selected == -1:
                    break

                # stagger
                sleep(0.05)
        except KeyboardInterrupt:
            print('\nclosing logviewer...')
        finally:
            print('\33[?25h', end='')
            log.close()