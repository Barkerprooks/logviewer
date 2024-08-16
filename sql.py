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
    
    os.unlink(db_path) # we rebuild the database each time we run. probably not super efficient

    connection = sqlite3.connect(db_path)
    
    with open(schema_path, 'rt') as file:
        connection.executescript(file.read())
    
    return connection


def insert_request(db: sqlite3.Connection, request: dict, commit: bool = True):
    # i know... shadowing the name 'request' is confusing... but i like the way it looks
    ip, date, time, size, agent, status, payload, request = request.values()
    method, route, proto = request.values()

    db.execute('INSERT INTO requests VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (
        ip, 
        agent, 
        status, 
        method, 
        route, 
        proto, 
        payload, 
        date, 
        time, 
        size
    ))

    # as a double measure insert the relevent info into the user-agent db
    db.execute('INSERT INTO user_agents VALUES (?, ?)', (
        ip,
        agent
    ))

    if commit:
        db.commit()


def insert_identity(db: sqlite3.Connection, ip: str, stats: dict, commit: bool = False):

    requests, lastseen, created = stats.values()

    db.execute('INSERT OR IGNORE INTO identities VALUES (?, ?, ?, ?)', (
        ip,
        requests,
        lastseen,
        created
    ))

    if commit:
        db.commit()


def update_identity(db: sqlite3.Connection, ip: str, stats: dict, commit: bool = False):
    
    requests, lastseen, _ = stats.values()

    db.execute('UPDATE identities SET requests = ?, lastseen = ? WHERE ip = ?', (
        requests,
        lastseen,
        ip
    ))

    if commit:
        db.commit()


def get_top_identities():
    ...
