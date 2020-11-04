
############################################################
# Json file <-> PostgreSQL command-line utility class      #
############################################################

import json
import sys

from classes.dbconn import DBConn

DEBUG = True

class JsonDB(object):

    def __init__(self, settings):
        self.settings = settings

    ####################################################################
    # Clear database
    ####################################################################
    def db_clear(self):
        db_conn = DBConn(self.settings)
        query = ("DELETE FROM " + self.settings["TABLE_SENSORS"] )
        db_conn.dbwrite(query,None)

    ####################################################################
    # Report database status
    ####################################################################
    def db_status(self):
        db_conn = DBConn(self.settings)
        query = "SELECT COUNT(*) FROM {}".format(self.settings["TABLE_SENSORS"])
        rows = db_conn.dbread(query,None)
        print("rows in {} {}".format(self.settings["TABLE_SENSORS"],rows))

    ####################################################################
    # db_write Import JSON -> Database
    ####################################################################
    def db_write(self, json_filename):
        with open(json_filename, 'r') as test_sensors:
            sensors_data = test_sensors.read()

        # parse file
        sensors = json.loads(sensors_data)

        print("loaded {}".format(json_filename))

        print(sensors)

        db_conn = DBConn(self.settings)

        for acp_id in sensors:
            query = "INSERT INTO " + self.settings["TABLE_SENSORS"] + " (acp_id, sensor_info) VALUES (%s, %s)"
            query_args = ( acp_id, json.dumps(sensors[acp_id]))
            try:
                db_conn.dbwrite(query, query_args)
            except:
                if DEBUG:
                    print(sys.exc_info())

    ####################################################################
    # db_read Export database -> JSON (latest records only)
    ####################################################################
    def db_read(self, json_filename):
        db_conn = DBConn(self.settings)
        # To select *all* the latest sensor objects:
        query = ("SELECT acp_id, sensor_info FROM " + self.settings["TABLE_SENSORS"]
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
    def db_readall(self, json_filename):
        db_conn = DBConn(self.settings)
        # To select *all* the latest sensor objects:
        query = "SELECT acp_id, sensor_info FROM " + self.settings["TABLE_SENSORS"]
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
