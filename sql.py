from log import parse_log_lines
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


def _update_address(db: sqlite3.Connection, address: str, visits: int, timestamp: str):
    db.execute('UPDATE addresses SET visits = ?, updated = ? WHERE ip = ?', (visits, timestamp, address))


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


# query data

def _get_last_n_hours_requests(db: sqlite3.Connection, hours: int) -> tuple:
    return db.execute("SELECT * FROM requests WHERE DATE(created) = DATE('now', '- ? hour')", (hours ,)).fetchall()


def _get_total_address_visits(db: sqlite3.Connection, ip: str) -> tuple:
    return db.execute("SELECT *, (SELECT COUNT(*) FROM requests WHERE ip = ?) AS visits FROM addresses where ip = ?", (ip, ip)).fetchone()


def query_db(db_path: str, query: str, **kwargs: dict) -> tuple:
    db = sqlite3.connect(db_path)

    if query == 'total_address_visits':
        return _get_total_address_visits(db, kwargs['ip'])

    if query == 'last_n_hours':
        return _get_last_n_hours_requests(db, kwargs['hours'] if not isinstance(kwargs['hours'], int) else 24)

    db.close()