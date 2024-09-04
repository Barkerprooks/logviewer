from logviewer.sql import initialize_db, query_db
from logviewer.cli import Raw, NonBlocking
from argparse import ArgumentParser
from time import sleep
from sys import stdin


argument_parser = ArgumentParser()
argument_parser.add_argument('-db', '--database', type=str, default='./db/logviewer.db')
argument_parser.add_argument('-s', '--schema', type=str, default='./db/schema.sql')
argument_parser.add_argument('-l', '--log', type=str, default='/var/log/nginx/website.log')

args = argument_parser.parse_args()

initialize_db(args.database, args.schema, args.log)

with Raw(stdin):
    with NonBlocking(stdin):
        while 1:
            # read new lines from log file in new thread
            # TODO (needs to be async somehow...)
            
            # handle input
            try:
                key = stdin.read(1)
                if key.isnumeric():
                    print('\33[2J', end='')
                    for row in query_db(args.database, 'last_n_hours', hours=int(key)):
                        print(row)
                    print(f'^ requests from the last {key} hour(s)')
            except IOError:
                print('stdin not ready')
            sleep(.1)