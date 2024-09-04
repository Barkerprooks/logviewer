from logviewer.log import parse_log_lines
from io import TextIOWrapper
from sqlite3 import connect, Connection
import os

'''
Jon Parker Brooks - 8/15/24


This file's purpose is to provide a simple API for updating the database
We need to:
- add requests, identities and user agents to their respective tables
- generate reports of the data held in the database
'''


# add data

def _insert_request(db: Connection, request: dict):
    db.execute('INSERT INTO requests VALUES (?,?,?,?,?,?,?)', tuple(request.values()))


def _insert_address(db: Connection, ip: str, timestamp: str):
    db.execute('INSERT OR IGNORE INTO addresses VALUES (?,?,?)', (ip, timestamp, timestamp))


def _insert_user_agent(db: Connection, agent: str, ip: str):
    db.execute('INSERT OR IGNORE INTO user_agents VALUES (?,?)', (agent, ip))


# setup db

def initialize_db(db_path: str, schema_path: str, log_path: str) -> TextIOWrapper:

    if os.path.isfile(db_path):
        os.unlink(db_path) # we rebuild the database each time we run. probably not super efficient

    db = connect(db_path) # create a new db
    with open(schema_path, 'rt') as file: # create the schema
        db.executescript(file.read())

    log = open(log_path, 'rb')

    for request in parse_log_lines(log):
        ip, created, agent = request['ip'], request['created'], request['user_agent']
        _insert_address(db, ip, created)
        _insert_user_agent(db, agent, ip)
        _insert_request(db, request)
    
    db.commit()
    db.close()

    return log


def insert_db(db_path: str, log: dict):
    
    db = connect(db_path) # connect to hopefully existing db
    ip, created, agent = log['ip'], log['created'], log['user_agent']

    _insert_request(db, log)
    _insert_address(db, ip, created)
    _insert_user_agent(db, agent, ip)

    db.commit()
    db.close()


# query data

def _get_all_requests(db: Connection) -> tuple:
    return tuple(db.execute('SELECT * FROM requests ORDER BY created DESC').fetchall())


def _get_all_requests_last_n_hours(db: Connection, hours: int) -> tuple:
    return tuple(db.execute("SELECT * FROM requests WHERE DATETIME(created) >= DATETIME('now', '-' || ? || ' hours') ORDER BY created DESC", (hours ,)).fetchall())


def _get_address_requests(db: Connection, ip: str) -> tuple:
    return tuple(db.execute('SELECT * FROM requests WHERE ip = ? ORDER BY DESC', (ip, )).fetchall())


def _get_address_requestst_last_n_hours(db: Connection, ip: str, hours: int) -> tuple:
    return tuple(db.execute("SELECT * FROM requests WHERE DATETIME(created) >= DATETIME('now', '-' || ? || ' hours') AND ip = ? ORDER BY created DESC", (hours, ip)).fetchall())


def _get_all_addresses(db: Connection) -> tuple:
    return tuple(db.execute('SELECT * FROM addresses ORDER BY updated DESC').fetchall())


def _get_address_details(db: Connection, ip: str) -> tuple:
    return tuple(db.execute('SELECT *, (SELECT COUNT(*) FROM requests WHERE ip = ?) AS visits FROM addresses where ip = ?', (ip, ip)).fetchone() or ())


def _get_address_user_agents(db: Connection, ip: str) -> tuple:
    return tuple(row[0] for row in db.execute('SELECT user_agent FROM user_agents WHERE ip = ?', (ip, )).fetchall())


def query_db(db_path: str, query: str, **kwargs: dict) -> tuple:
    db = connect(db_path)
    result = ()

    if query == 'all_requests':
        result = _get_all_requests(db)
    elif query == 'all_requests_last_n_hours': # by default return the last 24 hours
        result = _get_all_requests_last_n_hours(db, kwargs.get('hours', 24))
    elif query == 'address_requests':
        result = _get_address_requests(db, kwargs['ip']) # crash if ip not supplied
    elif query == 'address_requests_last_n_hours':
        result = _get_address_requestst_last_n_hours(db, kwargs['ip'], kwargs.get('hours', 24))
    elif query == 'address_details':
        result = _get_address_details(db, kwargs['ip'])
    elif query == 'all_addresses':
        result = _get_all_addresses(db)

    db.close()

    return result