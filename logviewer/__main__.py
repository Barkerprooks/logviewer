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


def handle_tui(db_path: str, key: str, tui: list) -> list:
    if key == '1':
        return list(query_db(db_path, 'all_requests'))
    elif key == '2':
        return list(query_db(db_path, 'all_requests_last_n_hours', hours=1))
    elif key == '3':
        return list(query_db(db_path, 'all_requests_last_n_hours', hours=6))
    elif key == '4':
        return list(query_db(db_path, 'all_requests_last_n_hours', hours=12))    
    elif key == '5':
        return list(query_db(db_path, 'all_requests_last_n_hours', hours=24))
    return tui


def handle_input(key: str, selected: int, tui_list_length: int) -> int:
    if key == 'w' and selected > 1:
        return selected - 1
    elif key == 's' and selected < tui_list_length - 1:
        return selected + 1
    elif key == 'q':
        return -1
    elif key.isnumeric():
        return 1
    return selected

def build_requests_output(selected, tui_list, tui_list_length, w, h):
    
    for y in range(h):
        if y == 0:
            print(('#' * (w - len(args.log) - 7)), args.log, end=' #####', flush=True)
        elif y < tui_list_length:
            try:
                ip, created, request, response, _, _, _ = tui_list[y - 1]
                method, route, _ = request.split(' ')
                timestamp = datetime.fromisoformat(created).strftime('%m/%d/%y %I:%M:%S %p')
                line = f'{method.ljust(8 if selected == y else 10, ' ')} {response} - {ip.rjust(15, ' ')}'
                if len(line + ' ' + timestamp) < w - 2:
                    line += ' ' + timestamp
                if len(line + ' ' + route) < w - 2:
                    line += ' ' + route
                if selected == y:
                    line = '> \33[34m' + line + '\33[0m'
                print(line, end=' ' * (w - len(line)), flush=True)
            except IndexError:
                print('...', end=' ' * (w - 3), flush=True)
        elif y == h - 2:
            mapping_line = '##### 1=12hr,2=24hr,3=1hr,4=all,5=addresses '
            print(mapping_line, end='#' * (w - len(mapping_line)), flush=True)
        elif y == h - 1:
            summary_line = f'##### total requests: {len(tui_list)} ##### q=quit,w=up,s=down '
            print(summary_line, end='#' * (w - len(summary_line)), flush=True)
        else:
            print(' ' * w, end='', flush=True)
        print(f'\33[{w}D\33[1B', end='', flush=True)
    print(f'\33[{h}A', end='', flush=True)


mode = 'all_requests'

log = initialize_db(args.database, args.schema, args.log)
tui = list(query_db(args.database, mode))
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
                    if mode == 'all_requests' or mode == 'all_requests_last_n_hours':
                        tui.insert(0, request.values())

                tui_list_length = h - (h // 3)
                tui_list = tui[:tui_list_length]

                if selected >= tui_list_length: # make sure cursor is in bounds
                    selected = tui_list_length - 1

                try:
                    if key := sys.stdin.read(1):
                        selected = handle_input(key, selected, tui_list_length)
                        tui = handle_tui(args.database, key, tui)
                except IOError:
                    print('stdin not ready')
                    break
                
                build_requests_output(selected, tui, tui_list_length, w, h)

                if selected == -1:
                    break

                # stagger
                sleep(0.02)
        except KeyboardInterrupt:
            print('\nclosing logviewer...')
        finally:
            print('\33[?25h', end='')
            log.close()