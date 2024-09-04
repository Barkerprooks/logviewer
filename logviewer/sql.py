from logviewer.log import parse_log_lines
import sqlite3
import os

'''
Jon Parker Brooks - 8/15/24


This file's purpose is to provide a simple API for updating the database
We need to:
- add requests, identities and user agents to their respective tables
- generate reports of the data held in the database
'''


# add data

def _insert_request(db: sqlite3.Connection, request: dict):
    db.execute('INSERT INTO requests VALUES (?,?,?,?,?,?,?)', tuple(request.values()))


def _insert_address(db: sqlite3.Connection, ip: str, timestamp: str):
    db.execute('INSERT OR IGNORE INTO addresses VALUES (?,?,?)', (ip, timestamp, timestamp))


def _insert_user_agent(db: sqlite3.Connection, agent: str, ip: str):
    db.execute('INSERT OR IGNORE INTO user_agents VALUES (?,?)', (agent, ip))


# setup db

def initialize_db(db_path: str, schema_path: str, log_path: str):

    if os.path.isfile(db_path):
        os.unlink(db_path) # we rebuild the database each time we run. probably not super efficient

    db = sqlite3.connect(db_path) # create a new db
    with open(schema_path, 'rt') as file: # create the schema
        db.executescript(file.read())

    for log in parse_log_lines(log_path):
        ip, created, agent = log['ip'], log['created'], log['user_agent']
        _insert_address(db, ip, created)
        _insert_user_agent(db, agent, ip)
        _insert_request(db, log)
    
    db.commit()
    db.close()


def insert_db(db_path: str, log: dict):
    
    db = sqlite3.connect(db_path) # connect to hopefully existing db
    ip, created, agent = log['ip'], log['created'], log['user_agent']

    _insert_request(db, log)
    _insert_address(db, ip, created)
    _insert_user_agent(db, agent, ip)

    db.commit()
    db.close()


# query data

def _get_all_last_n_hours(db: sqlite3.Connection, hours: int) -> tuple:
    return tuple(db.execute("SELECT * FROM requests WHERE DATETIME(created) >= DATETIME('now', '-' || ? || ' hours')", (hours ,)).fetchall())


def _get_last_n_hours(db: sqlite3.Connection, ip: str, hours: int) -> tuple:
    return tuple(db.execute("SELECT * FROM requests WHERE DATETIME(created) >= DATETIME('now', '-' || ? || ' hours') AND ip = ?", (hours, ip)).fetchall())


def _get_address_details(db: sqlite3.Connection, ip: str) -> tuple:
    return tuple(db.execute('SELECT *, (SELECT COUNT(*) FROM requests WHERE ip = ?) AS visits FROM addresses where ip = ?', (ip, ip)).fetchone() or ())


def _get_address_user_agents(db: sqlite3.Connection, ip: str) -> tuple:
    return tuple(row[0] for row in db.execute('SELECT user_agent FROM user_agents WHERE ip = ?', (ip, )).fetchall())


def query_db(db_path: str, query: str, **kwargs: dict) -> tuple:
    db = sqlite3.connect(db_path)
    result = ()

    if query == 'last_n_hours':
        ip, hours = kwargs.get('ip', None), kwargs.get('hours', 24)
        result = _get_all_last_n_hours(db, hours) if ip is None else _get_last_n_hours(db, ip, hours)
    elif query == 'address_details':
        result = _get_address_details(db, ip=kwargs.get('ip', ''))
    elif query == 'address_user_agents':
        result = _get_address_user_agents(db, ip=kwargs.get('ip', ''))

    db.close()

    return result