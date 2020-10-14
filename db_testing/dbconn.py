import psycopg2

class DBConn(object):

    def __init__(self, settings):
        self.settings = settings

    # Query the database and return the results
    def dbread(self, query):
        con = psycopg2.connect(database=self.settings["PGDATABASE"],
                                user=self.settings["PGUSER"])

        cur = con.cursor()
        cur.execute(query)
        rows = cur.fetchall()
        con.close()
        return rows

    # Execute the write query and commit the results
    def dbwrite(self, query):
        con = psycopg2.connect(database=self.settings["PGDATABASE"],
                                user=self.settings["PGUSER"])

        cur = con.cursor()
        cur.execute(query)
        con.commit()
        con.close()
