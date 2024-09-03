from logviewer.sql import initialize_db, query_db
from argparse import ArgumentParser


argument_parser = ArgumentParser()
argument_parser.add_argument('-db', '--database', type=str, default='./db/logviewer.db')
argument_parser.add_argument('-s', '--schema', type=str, default='./db/schema_v2.sql')
argument_parser.add_argument('-l', '--log', type=str, default='/var/log/nginx/website.log')

args = argument_parser.parse_args()

initialize_db(args.database, args.schema, args.log)

print('+ requests within the last 3 hours')
for ip, timestamp, request, status, length, user_agent, body in query_db(args.database, 'last_n_hours', hours=3):
    print(' -', status, '-', ip, request, user_agent)