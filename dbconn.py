import psycopg2
from CONFIG import *

def dbread(query):
    con = psycopg2.connect(database=PGDATABASE,
                            user=PGUSER)

    cur = con.cursor()
    cur.execute(query)
    rows = cur.fetchall()
    con.close()
    return rows

def dbwrite(query):
    con = psycopg2.connect(database=PGDATABASE,
                            user=PGUSER)

    cur = con.cursor()
    cur.execute(query)
    con.commit()
    con.close()