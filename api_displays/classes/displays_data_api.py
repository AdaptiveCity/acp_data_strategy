
from os import listdir, path
import json
import copy # used for JSON deepcopy
from collections import defaultdict
import sys
from datetime import datetime
import time
from flask import request
import requests
import importlib
from classes.dbconn import DBConn

# NOTE we also have "load_coordinate_systems()" which will dynamically import modules from acp_coordinates

DEBUG = True

###################################################################
#
# Displays DataAPI
#
###################################################################

DISPLAYS=None

class DisplaysDataAPI(object):

    def __init__(self, settings):
        global DISPLAYS
        print("Initializing Displays DataAPI")
        self.settings = settings

        self.db_conn = DBConn(self.settings)

        DISPLAYS = self.load_displays()
        print("Loaded Displays table")

        # Import acp_coordinates Python modules for each coordinate system listed in settings.json.
        self.load_coordinate_systems()

    #####################################################################
    #  METHODS CALLED FROM API                                          #
    #####################################################################

    # Takes in display_id and returns the display's information
    def get(self, display_id):
        global DISPLAYS

        if DEBUG:
            print("get {}".format(display_id), file=sys.stdout)

        # Read the display from the DATABASE, purely to refresh the in-memory cache (Displays)
        display_info = self.db_lookup_display(display_id)

        return display_info

    # Get the full history of metadata for a given display
    # This method will necessarily read the data from the database.
    def get_history(self, display_id):
        print(f"get_history {display_id}",file=sys.stderr, flush=True)
        global DISPLAYS
        try:
            # returns { 'history': [  <list of sensor_info objects> ] }
            history = self.db_lookup_display_history(display_id)
        except:
            print(f"get_history() error display_id {display_id}",file=sys.stderr, flush=True)
            return {}
        return { 'history': history }

    # Updates metadata for display object <display_id>
    def update(self, display_id, display_metadata):
        if "display_id" not in display_metadata or display_id != display_metadata["display_id"]:
            print(f'update { display_id } wrong display_id in display_metadata',file=sys.stderr,flush=True)
            return f'{{ "acp_error": "api_displays bad display_id {display_id} in display metadata" }}'

        try:
            self.write_obj(display_id, display_metadata)
        except:
            print(f'Error /update/{ display_id }/',file=sys.stderr,flush=True)
            print(f'{ json.dumps(display_metadata, indent=4) }', file=sys.stderr, flush=True)
            print( sys.exc_info() )
            return { "acp_error": "api_displays db write failed" }

        # Update in-memory entry
        DISPLAYS[display_id] = display_metadata
        print(f'update { display_id } updated',file=sys.stderr,flush=True)
        return {}


    ###########################################################################
    #
    # Support functions
    #
    ###########################################################################

    # Load ALL the Displays data from the store
    def load_displays(self):

        # To select *all* the latest sensor objects:
        query = "SELECT display_id, display_info FROM displays WHERE acp_ts_end IS NULL"

        try:
            displays_data = {}
            rows = self.db_conn.dbread(query, None)
            for row in rows:
                id, json_info = row
                displays_data[id] = json_info

        except:
            print(sys.exc_info(),flush=True,file=sys.stderr)
            return {}

        return displays_data

    # Return metadata from DATABASE for a single display
    # and update entry in-memory cache (BIM_data).
    def db_lookup_display(self, displays_id):
        global DISPLAYS

        query = "SELECT display_info FROM displays WHERE display_id=%s AND acp_ts_end IS NULL"
        query_args = (displays_id,)

        try:
            display_info = {}
            rows = self.db_conn.dbread(query, query_args)
            if len(rows) != 1:
                return None
            display_info = rows[0][0]
        except:
            print(sys.exc_info(),flush=True,file=sys.stderr)
            return None

        # Refresh in-memory copy
        DISPLAYS[displays_id] = display_info

        return display_info

    # Return all history for a given display as list
    def db_lookup_display_history(self, display_id):
        query = "SELECT record_id, display_info FROM displays WHERE display_id=%s ORDER BY acp_ts_end DESC"
        query_args = (display_id,)

        try:
            rows = self.db_conn.dbread(query, query_args)
            if len(rows) == 0:
                return None
            history = []
            for row in rows:
                ( record_id, info) = row
                info["acp_record_id"] = record_id # Embed the record_id
                history.append(info)
        except:
            print(sys.exc_info(),flush=True,file=sys.stderr)
            return None

        return history

    ####################################################################
    # Load the coordinate system modules into self.coordinate_systems  #
    ####################################################################

    def load_coordinate_systems(self):
        # this could be implemented like acp_decoders
        sys.path.append("..")

        self.coordinate_systems = {}

        for csystem in self.settings["coordinate_systems"]:
            import_string = "acp_coordinates."+csystem
            cmodule = importlib.import_module(import_string)
            cclass = getattr(cmodule, csystem)
            self.coordinate_systems[csystem] = cclass()

    ###################################################################################################################
    # write_obj - inserts a new database object record (used by db_write, db_merge)
    #   id:            the object identifier, e.g. "ijl20-sodaq-ttn"
    #   json_info_obj: the JSON information payload defining object
    #   db_table:      the 'TABLES' object from settings.json that gives the column names
    #   merge:         boolean that controls whether to "write" the json_info_obj or "merge" it into existing record.
    ###################################################################################################################

    def write_obj(self, id, json_info_obj, table_name="displays", id_name="display_id", json_name="display_info", merge=False):

        print(f'write_obj {id} {json_info_obj}')

        if id_name not in json_info_obj:
            print(f'Bad input, {id_name} not in json_info:\n{json_info_obj}', file=sys.stderr)
            return

        if json_info_obj[id_name] != id:
            print(f'Bad input, {id_name} {id} does not match in json_info:\n{json_info_obj}', file=sys.stderr)
            return

        # Create a datetime version of the "acp_ts" record timestamp
        if "acp_ts" in json_info_obj:
            update_acp_ts = datetime.fromtimestamp(float(json_info_obj["acp_ts"]))
        else:
            update_acp_ts = datetime.now()
            json_info_obj["acp_ts"] = '{:.6f}'.format(datetime.timestamp(update_acp_ts))

        # Update existing record 'acp_ts_end' (currently NULL) to this acp_ts (ONLY IF NEW acp_ts is NEWER)
        # First get acp_ts of most recent entry for current is
        query = f'SELECT acp_ts,{json_name} FROM {table_name} WHERE {id_name}=%s AND acp_ts_end IS NULL'
        query_args = (id,)
        r = self.db_conn.dbread(query, query_args)
        # Go ahead and update/insert if no records found or this record is newer than most recent
        if len(r) == 0 or r[0][0] < update_acp_ts:
            # Update (optional) existing record with acp_ts_end timestamp
            update_json_info = {}
            if len(r) == 1:
                update_json_info = copy.deepcopy(r[0][1])
                # Add "acp_ts_end" timestamp to json info of previous record
                update_json_info.update( { 'acp_ts_end': '{:.6f}'.format(datetime.timestamp(update_acp_ts)) } )
                # Update (optional) existing record with acp_ts_end timestamp
                query = f'UPDATE {table_name} SET acp_ts_end=%s, {json_name}=%s WHERE {id_name}=%s AND acp_ts_end IS NULL'
                query_args = (update_acp_ts, json.dumps(update_json_info), id)
                self.db_conn.dbwrite(query, query_args)

            if merge and len(r) == 1:
                update_json_info.update(json_info_obj)
                del update_json_info["acp_ts_end"]
            else:
                update_json_info = json_info_obj

            # Add new entry with this acp_ts
            query = f'INSERT INTO {table_name} ({id_name}, acp_ts, {json_name})'+" VALUES (%s, %s, %s)"
            query_args = ( id, update_acp_ts, json.dumps(update_json_info))
            try:
                self.db_conn.dbwrite(query, query_args)
            except:
                if DEBUG:
                    print(sys.exc_info(),flush=True,file=sys.stderr)
        else:
            print(f'Skipping {id} (existing or newer record in table)',flush=True,file=sys.stderr)
