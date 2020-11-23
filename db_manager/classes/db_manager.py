
############################################################
# Json file <-> PostgreSQL command-line utility class      #
############################################################

import json
import sys
from datetime import datetime

from classes.dbconn import DBConn

DEBUG = True

"""
Reads/writes DB table: <id>,acp_ts,acp_ts_end,<json_info>

The <id> and <json_info> column names are defined in settings.json.

E.g. 'sensors' table is acp_id,acp_ts,acp_ts_end,sensor_info.
"""

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
        # Get table properties from settings.json
        table_name = db_table["table_name"]
        id_name = db_table["id"]
        json_info = db_table["json_info"]

        # General 'WHERE' clause if --id given
        where = " WHERE "+id_name+"='"+id+"'" if id else ""

        # Build/execute query for record count
        print("\nQuerying table {} {}:".format(table_name, where))
        db_conn = DBConn(self.settings)
        query = "SELECT COUNT(*) FROM {} {}".format(table_name, where)
        count = db_conn.dbread(query,None)[0][0]
        if count == 0:
            print("    zero rows found")
        else:
            print("    {} rows found".format(count))

            # Build/execute query for max_ts
            query = "SELECT MAX(acp_ts) FROM {} {}".format(table_name, where)
            max_ts = db_conn.dbread(query,None)[0][0]
            print("    most recent update: {}".format(max_ts))

            # Build/execute query for row with newest acp_ts
            if id:
                where = "WHERE {} = '{}' AND acp_ts_end IS NULL".format(id_name, id, table_name)
                query = "SELECT {},acp_ts,{} FROM {} {}".format(id_name,json_info,table_name, where)
            else:
                where = "WHERE acp_ts = (SELECT MAX(acp_ts) from {})".format(table_name)
                query = "SELECT {},acp_ts,{} from {} {}".format(id_name,json_info,table_name, where)

            ret_id, ret_acp_ts, ret_info = db_conn.dbread(query,None)[0]
            print("    newest entry:\n{}".format(ret_info))

            #print("{} rows in {}, latest {}".format(count,
            #                                        table_name,
            #                                        datetime.strftime(max_ts,"%Y-%m-%d %H:%M:%S")))

    ####################################################################
    # db_write Import JSON -> Database
    ####################################################################
    def db_write(self, json_filename, db_table):
        with open(json_filename, 'r') as json_sensors:
            sensors_data = json_sensors.read()

        table_name = db_table["table_name"]
        id_name = db_table["id"]
        json_info = db_table["json_info"]
        # parse file { "<id>" : { "<id_name>: "<id", ...} }
        obj_list = json.loads(sensors_data)

        print("db_write loaded {}".format(json_filename),flush=True,file=sys.stderr)

        #print(sensors)

        db_conn = DBConn(self.settings)

        for id in obj_list:
            # Create a datetime version of the "acp_ts" record timestamp
            if "acp_ts" in obj_list[id]:
                acp_ts = datetime.fromtimestamp(float(obj_list[id]["acp_ts"]))
            else:
                acp_ts = datetime.now()
                obj_list[id]["acp_ts"] = '{:.6f}'.format(datetime.timestamp(acp_ts))

            # Update existing record 'acp_ts_end' (currently NULL) to this acp_ts (ONLY IF NEW acp_ts is NEWER)
            # First get acp_ts of most recent entry for current is
            query = f'SELECT acp_ts FROM {table_name} WHERE {id_name}=%s AND acp_ts_end IS NULL'
            query_args = (id,)
            r = db_conn.dbread(query, query_args)
            # Go ahead and update/insert if no records found or this record is newer than most recent
            if len(r) == 0 or r[0][0] < acp_ts:
                # Update (optional) existing record with acp_ts_end timestamp
                query = f'UPDATE {table_name} SET acp_ts_end=%s WHERE {id_name}=%s AND acp_ts_end IS NULL'
                query_args = (acp_ts, id)
                db_conn.dbwrite(query, query_args)

                # Add new entry with this acp_ts
                query = f'INSERT INTO {table_name} ({id_name}, acp_ts, {json_info})'+" VALUES (%s, %s, %s)"
                query_args = ( id, acp_ts, json.dumps(obj_list[id]))
                try:
                    db_conn.dbwrite(query, query_args)
                except:
                    if DEBUG:
                        print(sys.exc_info(),flush=True,file=sys.stderr)
            else:
                print(f'Skipping {id} (existing or newer record in table)',flush=True,file=sys.stderr)

    ####################################################################
    # db_merge Merge JSON -> Database
    ####################################################################
    def db_merge(self, json_filename, db_table):
        with open(json_filename, 'r') as json_sensors:
            json_data = json_sensors.read()

        table_name = db_table["table_name"]
        id_name = db_table["id"]
        json_name = db_table["json_info"]
        # parse file { "<id>" : { "<id_name>: "<id", ...} }
        obj_list = json.loads(json_data)

        print("db_merge loaded {}".format(json_filename),flush=True,file=sys.stderr)

        db_conn = DBConn(self.settings)

        for id in obj_list:
            # Create a datetime version of the "acp_ts" record timestamp
            if "acp_ts" in obj_list[id]:
                update_acp_ts = datetime.fromtimestamp(float(obj_list[id]["acp_ts"]))
            else:
                update_acp_ts = datetime.now()
                obj_list[id]["acp_ts"] = '{:.6f}'.format(datetime.timestamp(update_acp_ts))

            # Update existing record 'acp_ts_end' (currently NULL) to this acp_ts (ONLY IF NEW acp_ts is NEWER)
            # First get acp_ts of most recent entry for current is
            query = f'SELECT acp_ts, {json_name} FROM {table_name} WHERE {id_name}=%s AND acp_ts_end IS NULL'
            query_args = (id,)
            r = db_conn.dbread(query, query_args)
            # Go ahead and update/insert if no records found or this info is newer than most recent
            if len(r) == 0 or r[0][0] < update_acp_ts:
                new_json_info = {}
                if len(r) == 1:
                    new_json_info = r[0][1]
                    # Update (optional) existing record with acp_ts_end timestamp
                    query = f'UPDATE {table_name} SET acp_ts_end=%s WHERE {id_name}=%s AND acp_ts_end IS NULL'
                    query_args = (update_acp_ts, id)
                    db_conn.dbwrite(query, query_args)

                # Here is where the JSON merge happens
                new_json_info.update(obj_list[id])

                # Add new entry with this acp_ts and merged json
                query = f'INSERT INTO {table_name} ({id_name}, acp_ts, {json_name})'+" VALUES (%s, %s, %s)"
                query_args = ( id, update_acp_ts, json.dumps(new_json_info))
                try:
                    db_conn.dbwrite(query, query_args)
                except:
                    if DEBUG:
                        print(sys.exc_info(),flush=True,file=sys.stderr)
            else:
                print(f'Skipping {id} (existing or newer record in table)',flush=True,file=sys.stderr)

    ####################################################################
    # db_read Export database -> JSON (latest records only)
    ####################################################################
    def db_read(self, json_filename, db_table, id):
        db_conn = DBConn(self.settings)

        if id:
            # To select the latest object for id
            query = "SELECT {},{} FROM {} WHERE acp_ts_end IS NULL AND {}='{}'".format(
                        db_table["id"],
                        db_table["json_info"],
                        db_table["table_name"],
                        db_table["id"],
                        id)
        else:
            # To select *all* the latest sensor objects:
            query = "SELECT {},{} FROM {} WHERE acp_ts_end IS NULL".format(
                        db_table["id"],
                        db_table["json_info"],
                        db_table["table_name"])

        try:
            result_obj = {}
            rows = db_conn.dbread(query, None)
            for row in rows:
                acp_id, sensor_info = row
                result_obj[acp_id] = sensor_info

            self.write_json(result_obj, json_filename)

        except:
            if DEBUG:
                print(sys.exc_info(),flush=True,file=sys.stderr)

    ####################################################################
    # db_read Export database -> JSON (latest records only)
    ####################################################################
    def db_readall(self, json_filename, db_table,id):
        db_conn = DBConn(self.settings)
        # To select *all* the latest sensor objects:
        if id:
            # To select the latest object for id
            query = "SELECT {},{} FROM {} WHERE {}='{}'".format(
                        db_table["id"],
                        db_table["json_info"],
                        db_table["table_name"],
                        db_table["id"],
                        id)
        else:
            # To select *all* the latest sensor objects:
            query = "SELECT {},{} FROM {}".format(
                        db_table["id"],
                        db_table["json_info"],
                        db_table["table_name"])

        try:
            result_list = []
            rows = db_conn.dbread(query, None)
            for row in rows:
                acp_id, sensor_info = row
                result_list.append( { 'acp_id': acp_id, 'sensor_info': sensor_info } )

            self.write_json(result_list, json_filename)

        except:
            if DEBUG:
                print(sys.exc_info(),flush=True,file=sys.stderr)

    ####################################################################
    # write_json: output a python dict to json file
    ####################################################################
    def write_json(self, json_obj, json_filename):
        with (open(json_filename,'w') if json_filename is not None else sys.stdout) as outfile:
            outfile.write(json.dumps(json_obj, sort_keys=True, indent=4)+'\n')

# End Class JsonDB
