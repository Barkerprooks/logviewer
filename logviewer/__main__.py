from logviewer.sql import initialize_db, query_db
from logviewer.cli import Raw, NonBlocking
from logviewer.log import parse_log
from argparse import ArgumentParser
from select import select
from time import sleep
from sys import stdin
from io import SEEK_END, TextIOWrapper


def handle_input(key: str):
    ...


argument_parser = ArgumentParser()
argument_parser.add_argument('-db', '--database', type=str, default='./db/logviewer.db')
argument_parser.add_argument('-s', '--schema', type=str, default='./db/schema.sql')
argument_parser.add_argument('-l', '--log', type=str, default='/var/log/nginx/website.log')

args = argument_parser.parse_args()

log = initialize_db(args.database, args.schema, args.log)

with Raw(stdin):
    with NonBlocking(stdin):
        while 1: # forever (until ctrl+c)

            # check if file has new things to read
            if line := log.readline():
                logline = parse_log(line)
                print(logline)

            try:
                if key := stdin.read(1):
                    handle_input(key)
            except IOError:
                print('stdin not ready')
            
            # stagger
            sleep(.01)