from logviewer.sql import initialize_db, query_db, insert_db
from logviewer.cli import Raw, NonBlocking
from logviewer.log import parse_log
from argparse import ArgumentParser
from os import get_terminal_size
from time import sleep
from datetime import datetime
from zoneinfo import ZoneInfo
import sys


argument_parser = ArgumentParser()
argument_parser.add_argument('-db', '--database', type=str, default='./db/logviewer.db')
argument_parser.add_argument('-s', '--schema', type=str, default='./db/schema.sql')
argument_parser.add_argument('-l', '--log', type=str, default='/var/log/nginx/website.log')

args = argument_parser.parse_args()


def handle_tui(db_path: str, key: str, tui: list, mode: str) -> tuple:
    if key == '1':
        return list(query_db(db_path, 'all_requests')), 'all_requests'
    elif key == '2':
        return list(query_db(db_path, 'all_requests_last_n_hours', hours=1)), 'all_requests_last_n_hours'
    elif key == '3':
        return list(query_db(db_path, 'all_requests_last_n_hours', hours=6)), 'all_requests_last_n_hours'
    elif key == '4':
        return list(query_db(db_path, 'all_requests_last_n_hours', hours=12)), 'all_requests_last_n_hours'
    elif key == '5':
        return list(query_db(db_path, 'all_requests_last_n_hours', hours=24)), 'all_requests_last_n_hours'
    elif key == '6':
        if mode == 'all_requests' or mode == 'all_requests_last_n_hours':
            return list(query_db(db_path, 'all_addresses')), 'all_addresses'
        elif mode == 'all_addresses':
            return list(query_db(db_path, 'all_requests')), 'all_requests'
    return tui, mode


def handle_input(key: str, selected: int, offset: int, tui_max_length: int, tui_list_length: int) -> int:
    if key == 'w' and selected > 1:
        if offset > 0:
            return selected, offset - 1
        else:
            return selected - 1, 0
    elif key == 's':
        if tui_list_length > tui_max_length:
            return 1, 0
        elif selected < tui_list_length - 1:
            return selected + 1, offset
        elif selected + offset < tui_max_length - 1:
            return selected, offset + 1
    elif key == 'q':
        return -1, 0
    elif key.isnumeric():
        return 1, 0
    return selected, offset


def build_addresses_output(selected: int, offset: int, tui: list, tui_list_length: int, w: int, h: int):
    for y in range(h):
        if y == 0:
            print(('=' * (w - len(args.log) - 7)), args.log, end=' =====', flush=True)
        elif y < tui_list_length:
            try:
                ip, updated, created = tui[y - 1 + offset]
                updated = datetime.fromisoformat(created).astimezone(ZoneInfo('America/Chicago')).strftime('%m/%d/%y %I:%M:%S %p')
                created = datetime.fromisoformat(created).astimezone(ZoneInfo('America/Chicago')).strftime('%m/%d/%y %I:%M:%S %p')
                line = f'{ip.ljust(15 if selected == y else 17, ' ')} - last: {updated}, first: {created}'
                if selected == y:
                    line = '> ' + line
                print(line, end=' ' * (w - len(line)), flush=True)
            except IndexError:
                print('-', end=' ' * (w - 1), flush=True)
        elif y == h - 3:
            line = f'request: {selected + offset} / {len(tui)}'
            print(('=' * (w - len(line) - 7)), line, end=' =====', flush=True)
        elif y == h - 2:
            line = '1: all, 2: 1hr, 3: 6hr, 4: 12hr, 5: 24hr, 6: address '
            print(line, end=' ' * (w - len(line)), flush=True)
        elif y == h - 1:
            line = 'q: quit, w: up, s: down '
            print(line, end=' ' * (w - len(line)), flush=True)
        else:
            print(' ' * w, end='', flush=True)
        print(f'\33[{w}D\33[1B', end='', flush=True)
    print(f'\33[{h}A', end='', flush=True)


def build_requests_output(selected: int, offset: int, tui: list, tui_list_length: int, w: int, h: int):
    
    for y in range(h):
        if y == 0:
            print(('=' * (w - len(args.log) - 7)), args.log, end=' =====', flush=True)
        elif y < tui_list_length:
            try:
                ip, created, request, response, _, _, _ = tui[y - 1 + offset]
                method, route, _ = request.split(' ')
                timestamp = datetime.fromisoformat(created).astimezone(ZoneInfo('America/Chicago')).strftime('%m/%d/%y %I:%M:%S %p')
                line = f'{method.ljust(8 if selected == y else 10, ' ')} {response} - {ip.rjust(15, ' ')}'
                if len(line + ' ' + timestamp) < w - 1:
                    line += ' ' + timestamp
                if len(line + ' ' + route) < w - 1:
                    line += ' ' + route
                if selected == y:
                    line = '> ' + line
                print(line, end=' ' * (w - len(line)), flush=True)
            except IndexError:
                print('-', end=' ' * (w - 1), flush=True)
        elif y == h - 3:
            line = f'request: {selected + offset} / {len(tui)}'
            print(('=' * (w - len(line) - 7)), line, end=' =====', flush=True)
        elif y == h - 2:
            line = '1: all, 2: 1hr, 3: 6hr, 4: 12hr, 5: 24hr, 6: address '
            print(line, end=' ' * (w - len(line)), flush=True)
        elif y == h - 1:
            line = 'q: quit, w: up, s: down '
            print(line, end=' ' * (w - len(line)), flush=True)
        else:
            print(' ' * w, end='', flush=True)
        print(f'\33[{w}D\33[1B', end='', flush=True)
    print(f'\33[{h}A', end='', flush=True)


mode = 'all_requests'

log = initialize_db(args.database, args.schema, args.log)
tui = list(query_db(args.database, mode))
selected = 1
offset = 0

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
                    if mode == 'all_requests' or mode == 'all_requests_last_n_hours':
                        tui.insert(0, request.values())

                tui_list_length = h - 4

                if selected >= tui_list_length: # make sure cursor is in bounds
                    selected = tui_list_length - 1

                try:
                    if key := sys.stdin.read(1):
                        selected, offset = handle_input(key, selected, offset, len(tui), tui_list_length)
                        tui, mode = handle_tui(args.database, key, tui, mode)
                except IOError:
                    print('stdin not ready')
                    break
                
                if mode == 'all_requests' or mode == 'all_requests_last_n_hours':
                    build_requests_output(selected, offset, tui, tui_list_length, w, h)
                elif mode == 'all_addresses':
                    build_addresses_output(selected, offset, tui, tui_list_length, w, h)

                if selected == -1:
                    break

                # stagger
                sleep(0.02)
        except KeyboardInterrupt:
            print('\nclosing logviewer...')
        finally:
            print('\33[?25h', end='')
            log.close()