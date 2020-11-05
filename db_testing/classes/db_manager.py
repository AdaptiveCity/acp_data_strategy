
############################################################
# Json file <-> PostgreSQL command-line utility class      #
############################################################

import json
import sys
from datetime import datetime

from classes.dbconn import DBConn

DEBUG = True

class DBManager(object):

    def __init__(self, settings):
        self.settings = settings

    ####################################################################
    # Clear database
    ####################################################################
    def db_clear(self, db_table, id):
        where = " WHERE "+db_table["id"]+"='"+id+"'" if id else ""
        db_conn = DBConn(self.settings)
        query = "DELETE FROM {} {}".format(db_table["table_name"], where)
        db_conn.dbwrite(query,None)

    ####################################################################
    # Report database status
    ####################################################################
    def db_status(self, db_table, id):
        table_name = db_table["table_name"]
        where = " WHERE "+db_table["id"]+"='"+id+"'" if id else ""
        db_conn = DBConn(self.settings)
        query = "SELECT COUNT(*) FROM {} {}".format(table_name, where)
        count = db_conn.dbread(query,None)[0][0]

        query = "SELECT MAX(acp_ts) FROM {} {}".format(table_name, where)
        max_ts = db_conn.dbread(query,None)[0][0]

        if id:
            query = "SELECT acp_ts FROM {} {} AND 'acp_ts_end' is NULL".format(table_name, where)

        where = " where acp_ts = (select MAX(acp_ts) from {})".format(table_name)
        query = "select acp_id,sensor_info->'acp_ts' from {} {}".format(table_name, where)
        ret = db_conn.dbread(query,None)
        print(ret)

        if count == 0:
            print("zero rows from {}".format(table_name))
        else:
            print("{} rows in {}, latest {}".format(count,
                                                table_name,
                                                datetime.strftime(max_ts,"%Y-%m-%d %H:%M:%S")))

    ####################################################################
    # db_write Import JSON -> Database
    ####################################################################
    def db_write(self, json_filename, db_table):
        with open(json_filename, 'r') as test_sensors:
            sensors_data = test_sensors.read()

        # parse file
        sensors = json.loads(sensors_data)

        print("loaded {}".format(json_filename))

        #print(sensors)

        db_conn = DBConn(self.settings)

        for acp_id in sensors:
            # Create a datetime version of the "acp_ts" record timestamp
            if "acp_ts" in sensors[acp_id]:
                acp_ts = datetime.fromtimestamp(float(sensors[acp_id]["acp_ts"]))
            else:
                acp_ts = datetime.now()

            query = "INSERT INTO " + db_table["table_name"] + " (acp_id, acp_ts, sensor_info) VALUES (%s, %s, %s)"
            query_args = ( acp_id, acp_ts, json.dumps(sensors[acp_id]))
            try:
                db_conn.dbwrite(query, query_args)
            except:
                if DEBUG:
                    print(sys.exc_info())

    ####################################################################
    # db_read Export database -> JSON (latest records only)
    ####################################################################
    def db_read(self, json_filename, db_table):
        db_conn = DBConn(self.settings)
        # To select *all* the latest sensor objects:
        query = ("SELECT acp_id, sensor_info FROM " + db_table["table_name"]
                 + " WHERE acp_ts_end IS NULL"
                )

        try:
            result_obj = {}
            rows = db_conn.dbread(query, None)
            for row in rows:
                acp_id, sensor_info = row
                result_obj[acp_id] = sensor_info

            self.write_json(result_obj, json_filename)

        except:
            if DEBUG:
                print(sys.exc_info())

    ####################################################################
    # db_read Export database -> JSON (latest records only)
    ####################################################################
    def db_readall(self, json_filename, db_table):
        db_conn = DBConn(self.settings)
        # To select *all* the latest sensor objects:
        query = "SELECT acp_id, sensor_info FROM " + db_table["table_name"]
        try:
            result_list = []
            rows = db_conn.dbread(query, None)
            for row in rows:
                acp_id, sensor_info = row
                result_list.append( { 'acp_id': acp_id, 'sensor_info': sensor_info } )

            self.write_json(result_list, json_filename)

        except:
            if DEBUG:
                print(sys.exc_info())

    ####################################################################
    # write_json: output a python dict to json file
    ####################################################################
    def write_json(self, json_obj, json_filename):
        with (open(json_filename,'w') if json_filename is not None else sys.stdout) as outfile:
            outfile.write(json.dumps(json_obj, sort_keys=True, indent=4)+'\n')

# End Class JsonDB
