import psycopg2
import psycopg2.extras
from os import environ as config

def initialize():
    global conn, c
    conn = psycopg2.connect(config['DATABASE_URL'], sslmode='require')
    c = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)

def close():
    global conn
    conn.close()

def commit():
    global conn
    return conn.commit()

def execute(*args, **kwargs):
    global conn, c
    try:
        return c.execute(*args, **kwargs)
    except:
        initialize()
        return c.execute(*args, **kwargs)

def fetchall():
    global c
    return c.fetchall()

def fetchone():
    global c
    return c.fetchone()

def rowcount():
    global c
    return c.rowcount

