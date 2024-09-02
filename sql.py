import sqlite3
import os

'''
Jon Parker Brooks - 8/15/24


This file's purpose is to provide a simple API for updating the database
We need to:
- add requests, identities and user agents to their respective tables
- generate reports of the data held in the database
'''

def load_db(db_path: str, schema_path: str):
    
    if os.path.isfile(db_path):
        os.unlink(db_path) # we rebuild the database each time we run. probably not super efficient

    connection = sqlite3.connect(db_path)
    
    with open(schema_path, 'rt') as file:
        connection.executescript(file.read())
    
    return connection


# v2

def insert_request(db: sqlite3.Connection, request: dict):
    db.execute('INSERT INTO requests VALUES (?,?,?,?,?,?,?)', tuple(request.values()))


def insert_address(db: sqlite3.Connection, ip: str, timestamp: str):
    db.execute('INSERT OR IGNORE INTO addresses VALUES (?,?,?,?)', (ip, 1, timestamp, timestamp))


def insert_user_agent(db: sqlite3.Connection, agent: str, ip: str):
    db.execute('INSERT OR IGNORE INTO user_agents VALUES (?,?)', (agent, ip))


def update_address(db: sqlite3.Connection, address: str, visits: int, timestamp: str):
    db.execute('UPDATE addresses SET visits = ?, updated = ? WHERE ip = ?', (visits, timestamp, address))