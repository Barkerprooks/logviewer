CREATE TABLE IF NOT EXISTS identities (
    ip TEXT UNIQUE,
    requests INTEGER,
    lastseen TEXT,
    created TEXT
);

CREATE TABLE IF NOT EXISTS user_agents (
    ip TEXT,
    user_agent TEXT,
    FOREIGN KEY(ip) REFERENCES identities(ip)
);

CREATE TABLE IF NOT EXISTS requests (
    ip TEXT,
    user_agent TEXT,
    request_status INTEGER,
    request_method TEXT,
    request_route TEXT,
    request_proto TEXT,
    request_payload TEXT,
    request_date TEXT,
    request_time TEXT,
    request_size INTEGER,
    FOREIGN KEY(user_agent) REFERENCES user_agents(user_agent),
    FOREIGN KEY(ip) REFERENCES identities(ip)
);