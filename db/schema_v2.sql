CREATE TABLE IF NOT EXISTS addresses (
    ip TEXT UNIQUE,
    visits INTEGER,
    updated TEXT,
    created TEXT
);

CREATE TABLE IF NOT EXISTS user_agents (
    user_agent TEXT,
    ip TEXT,
    FOREIGN KEY(ip) REFERENCES addresses(ip),
    PRIMARY KEY(user_agent, ip)
);

CREATE TABLE IF NOT EXISTS requests (
    ip TEXT,
    created TEXT,
    request TEXT,
    response INTEGER,
    bytes INTEGER,
    user_agent TEXT,
    body TEXT,
    FOREIGN KEY(ip) REFERENCES addresses(ip),
    FOREIGN KEY(user_agent) REFERENCES user_agents(user_agent)
);