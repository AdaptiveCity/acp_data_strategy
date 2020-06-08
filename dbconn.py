import psycopg2
from CONFIG import *

# Query the database and return the results
def dbread(query):
    con = psycopg2.connect(database=PGDATABASE,
                            user=PGUSER)

    cur = con.cursor()
    cur.execute(query)
    rows = cur.fetchall()
    con.close()
    return rows

# Execute the write query and commit the results
def dbwrite(query):
    con = psycopg2.connect(database=PGDATABASE,
                            user=PGUSER)

    cur = con.cursor()
    cur.execute(query)
    con.commit()
    con.close()