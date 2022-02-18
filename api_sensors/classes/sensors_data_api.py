from ast import arg
from os import listdir, path
import json
import copy # used for JSON deepcopy
from collections import defaultdict
import sys
from datetime import datetime
import time
import numpy
from flask import request, make_response
import importlib
import requests
from requests.exceptions import HTTPError
from classes.dbconn import DBConn

DEBUG = True

###################################################################
#
# SENSORS PostgreSQL DataAPI
#
###################################################################

SENSORS=None

SENSOR_TYPES=None

class SensorsDataAPI(object):

    def __init__(self, settings):
        # Declare Python dictionaries to hold ALL sensor and sensor_type metadata
        # These will be initialized by reading entire tables into each dictionary
        global SENSORS, SENSOR_TYPES

        print("Initializing SENSORS DataAPI")
        self.settings = settings

        # Establish connection to PostgreSQL
        self.db_conn = DBConn(self.settings)

        # Load sensor and sensor_types metadata
        SENSORS = self.db_load_sensors()
        SENSOR_TYPES = self.db_load_sensor_types()
        # print(f'Loaded sensor and sensor_types tables SENSOR_TYPES:{SENSOR_TYPES}')

        # Import acp_coordinates Python modules for each coordinate system listed in settings.json.
        self.load_coordinate_systems()

    # Get the metadata for a given sensor (e.g. 'rad-ath-003d0f'), including the type metadata
    # Note a 'get' of sensor metadata will read the DATABASE and refresh the entry in the SENSORS dictionary
    def get(self, acp_id, args):
        # print(f"get {acp_id}",file=sys.stderr, flush=True)

        global SENSORS, SENSOR_TYPES

        if 'person_id' in args:
            person_id = args['person_id']
            access_response = requests.get(self.settings['API_PERMISSIONS']+'/get_permission/'+person_id+'/'+acp_id+'/'+'sensors/read').json()

            if access_response['permission'] == False:
                json_response = json.dumps({'access_error': 'User '+person_id+ ' does not have access to sensor '+acp_id})
                response = make_response(json_response)
                response.headers['Content-Type'] = 'application/json'
                return response

        try:
            sensor_info = self.db_lookup_sensor(acp_id)
            # print(f'got db_lookup_sensor {sensor_info}', file=sys.stderr)
            if "acp_type_id" in sensor_info:
                acp_type_id = sensor_info["acp_type_id"]
                # print(f'Looking up acp_type_id {acp_type_id}', file=sys.stderr)
                if acp_type_id in SENSOR_TYPES:
                    sensor_info["acp_type_info"] = SENSOR_TYPES[acp_type_id]
                    # print(f'Got acp_type_info {sensor_info["acp_type_id"]}', file=sys.stderr)
        except:
            print(f"get() no sensor id {acp_id}",file=sys.stderr, flush=True)
            return {}

        print(f'Returning {sensor_info}', file=sys.stderr)

        return sensor_info

    # Get the full history of metadata for a given sensor (e.g. 'rad-ath-003d0f')
    # This method will necessarily read the data from the database (as the SENSORS dictionary only
    # contains the latest metadata record not the prior history).
    def get_history(self, acp_id):
        
        print(f"get_history {acp_id}",file=sys.stderr, flush=True)
        global SENSORS, SENSOR_TYPES
        try:
            # returns { 'sensor_history': [  <list of sensor_info objects> ], 'sensor_info': { <latest sensor_info> }
            sensor_history_obj = self.db_lookup_sensor_history(acp_id)
            # Add 'acp_type_info' to sensor_history_obj['sensor_info']
            if 'acp_type_id' in sensor_history_obj['sensor_info']:
                acp_type_id = sensor_history_obj['sensor_info']['acp_type_id']
                if acp_type_id in SENSOR_TYPES:
                    sensor_history_obj['acp_type_info'] = SENSOR_TYPES[acp_type_id]
        except:
            print(f"get() no sensor id {acp_id}",file=sys.stderr, flush=True)
            return {}
        return sensor_history_obj

    # Get the metadata for a given sensor TYPE (e.g. 'rad-ath')
    # Note a 'get_type' of sensor type metadata will read the DATABASE and refresh the entry in the SENSOR_TYPES dictionary
    def get_type(self, acp_type_id):
        print("get_type {}".format(acp_type_id))
        type_info = self.db_lookup_sensor_type(acp_type_id)
        return type_info if type_info is not None else {}

    # Get the full history of metadata for a given sensor type (e.g. 'elsys-co2')
    # This method will necessarily read the data from the database (as the SENSOR_TYPES dictionary only
    # contains the latest metadata record not the prior history).
    def get_type_history(self, acp_type_id):
        print(f"get_type_history {acp_type_id}",file=sys.stderr, flush=True)
        global SENSOR_TYPES
        try:
            # returns { 'history': [  <list of sensor_info objects> ] }
            history = self.db_lookup_sensor_type_history(acp_type_id)
        except:
            print(f"get_type_history() error sensor type id {acp_type_id}",file=sys.stderr, flush=True)
            return {}
        return { 'history': history }

    # /get_floor_number/<system>/<floor>[?metadata=true]
    # Returns:
    # { "sensors": { },
    #   "sensor_type_info" : { }
    # }
    #DEBUG get_floor_number should return ["sensor_types"] not ["sensor_type_info"]
    def get_floor_number(self, coordinate_system, floor_number, args):
        print("SENSORS data_api get_floor_number({},{})".format(coordinate_system, floor_number))
        sensor_list_obj = {}
        # coords.f(acp_location) will return floor number
        coords = self.coordinate_systems[coordinate_system]

        return_obj = {}

        for acp_id in SENSORS:
            #determine if the same floor

            sensor = SENSORS[acp_id]
            print("SENSORS api get_floor_number sensor={}".format(sensor))
            if "acp_location" in sensor:
                loc = sensor["acp_location"]
                if loc["system"] == coordinate_system and coords.f(loc) == int(floor_number):
                    access = True
                    try:
                        response = requests.get(self.settings["API_PERMISSIONS"]+f'get_permission/{args["person_id"]}/{acp_id}/sensor/read')
                        if response.json()['permission'] == False:
                            access = False
                    except KeyError as e:
                        print('KeyError: ',e)                    
                    if access:
                        sensor_list_obj[acp_id] = sensor

        

        self.add_xyzf(coordinate_system, sensor_list_obj)

        return_obj["sensors"] = sensor_list_obj

        # Iterate through the sensors and add sensor_type_info for each
        sensor_type_info = {}
        for acp_id in sensor_list_obj:
            sensor = sensor_list_obj[acp_id]
            if "acp_type_id" in sensor:
                sensor_type_id = sensor["acp_type_id"]
                if sensor_type_id in SENSOR_TYPES and sensor_type_id not in sensor_type_info:
                    sensor_type_info[sensor_type_id] = SENSOR_TYPES[sensor_type_id]

        return_obj["sensor_type_info"] = sensor_type_info

        return return_obj

    # Get sensors for a given crate_id, returning dictionary of sensors
    def get_bim(self, coordinate_system, crate_id):
        #iterate through sensors.json and collect all crates
        sensor_list_obj = {}

        for acp_id in SENSORS:
            
            sensor = SENSORS[acp_id]
            if ( "crate_id" in sensor and
                sensor["crate_id"] == crate_id ):
                sensor_list_obj[acp_id] =  sensor

        self.add_xyzf(coordinate_system, sensor_list_obj)

        return { 'sensors': sensor_list_obj }

    #DEBUG this function needs parameters or renaming
    #DEBUG moved from space API
    # Note we are using a 'list_obj', i.e. { "id1": { "acp_id": "id1", ..}, "id2": { "acp_id": "id2", ...} }
    def get_gps(self, args):
        sensor_list_obj = {}


        for acp_id in SENSORS:
            sensor = SENSORS[acp_id]
            if ( "acp_location" in sensor and
                sensor["acp_location"]["system"] == "GPS" ):
                sensor_list_obj[acp_id] = sensor

        return { 'sensors': sensor_list_obj }

    # Return a list of sensor's metadata
    # Returns { sensors: [..], types: [..]}
    def list(self, args):
        # debug listing of querystring args
        if DEBUG:
            args_str = ""
            for key in args:
                args_str += key+"="+args.get(key)+" "
            print("list() {}".format(args_str) )
        # Set bool to include sensor type metadata
        include_type_info = "type_metadata" in args and args["type_metadata"] == "true"
        sensor_list_obj = {}
        type_list_obj = {}

        for acp_id in SENSORS:
            sensor = SENSORS[acp_id]

            if True:                   # Here's where we'd filter the results
                sensor_list_obj[acp_id] = sensor
                if include_type_info and "acp_type_id" in sensor:
                    acp_type_id = sensor["acp_type_id"]
                    type_info = self.type_lookup(acp_type_id)
                    if type_info is not None:
                        type_list_obj[acp_type_id] = type_info

        # Build return object { sensors: [..], types: [..]}
        return_obj = { 'sensors': sensor_list_obj }
        if include_type_info:
            return_obj["types"] = type_list_obj

        return return_obj

    # Return a list of sensor type  metadata
    # Returns { types: { "elsys-ems": {...}, ... }}
    def list_types(self, args):
        # debug listing of querystring args
        if DEBUG:
            args_str = ""
            for key in args:
                args_str += key+"="+args.get(key)+" "
            print("list_types() {}".format(args_str) )
        # Set bool to include sensor type metadata
        type_list_obj = {}
        for acp_type_id in SENSOR_TYPES:
            if True:                   # Here's where we'd filter the results
                type_info = self.type_lookup(acp_type_id)
                type_list_obj[acp_type_id] = type_info

        return_obj = { }
        return_obj["types"] = type_list_obj

        return return_obj

    # Updates metadata for sensor <acp_id>
    def update(self, acp_id, sensor_metadata):
        if "acp_id" not in sensor_metadata or acp_id != sensor_metadata["acp_id"]:
            print(f'update { acp_id } wrong acp_id in sensor_metadata',file=sys.stderr,flush=True)
            return { "acp_error": "api_sensors bad acp_id in sensor metadata" }

        try:
            self.write_obj(acp_id, sensor_metadata)
        except:
            print(f'update { acp_id }',file=sys.stderr,flush=True)
            print(f'{ json.dumps(sensor_metadata, indent=4) }', file=sys.stderr, flush=True)
            return { "acp_error": "api_sensors db write failed" }

        print(f'update { acp_id } updated',file=sys.stderr,flush=True)
        # Update in-memory entry
        SENSORS[acp_id] = sensor_metadata
        return {}

    # Updates metadata for sensor type <acp_type_id>
    def update_type(self, acp_type_id, sensor_type_metadata):
        if "acp_type_id" not in sensor_type_metadata or acp_type_id != sensor_type_metadata["acp_type_id"]:
            print(f'update_type { acp_type_id } wrong acp_type_id in sensor_type_metadata',file=sys.stderr,flush=True)
            return { "acp_error": "api_sensors bad acp_type_id in sensor type metadata" }

        try:
            self.write_type_obj(acp_type_id, sensor_type_metadata)
        except:
            print(f'update_type { acp_type_id }',file=sys.stderr,flush=True)
            print(f'{ json.dumps(sensor_type_metadata, indent=4) }', file=sys.stderr, flush=True)
            return { "acp_error": "api_sensors db write failed" }

        # Update in-memory entry
        SENSOR_TYPES[acp_type_id] = sensor_type_metadata
        print(f'update_type { acp_type_id } updated',file=sys.stderr,flush=True)
        return {}

    ###########################################################################
    #
    # Support functions
    #
    ###########################################################################

    # This loads the sensor metadata into memory - we could use a database live instead.
    def db_load_sensors(self):

        # To select *all* the latest sensor objects:
        query = "SELECT acp_id,sensor_info FROM sensors WHERE acp_ts_end IS NULL"

        try:
            sensors = {}
            rows = self.db_conn.dbread(query, None)
            for row in rows:
                id, json_info = row
                sensors[id] = json_info

        except:
            print(sys.exc_info(),flush=True,file=sys.stderr)
            return {}

        return sensors

    def db_load_sensor_types(self):
        # To select *all* the latest sensor objects:
        # print(f'db_load_sensor_types()', file=sys.stderr)
        query = "SELECT acp_type_id, type_info FROM sensor_types WHERE acp_ts_end IS NULL"

        try:
            sensor_types = {}
            rows = self.db_conn.dbread(query, None)
            # print(f'db_load_sensor_types() loaded {len(rows)} rows', file=sys.stderr)
            for row in rows:
                id, json_info = row
                sensor_types[id] = json_info
                # print(f'db_load_sensor_types() loaded {sensor_types[id]}', file=sys.stderr)

        except:
            print(sys.exc_info(),flush=True,file=sys.stderr)
            return {}

        return sensor_types

    # Return metadata from DATABASE for a single sensor
    def db_lookup_sensor(self, acp_id):

        query = "SELECT sensor_info FROM sensors WHERE acp_id=%s AND acp_ts_end IS NULL"
        query_args = (acp_id,)

        try:
            sensor_info = {}
            rows = self.db_conn.dbread(query, query_args)
            if len(rows) != 1:
                return None
            sensor_info = rows[0][0]

        except:
            print(sys.exc_info(),flush=True,file=sys.stderr)
            return None

        SENSORS[acp_id] = sensor_info
        return sensor_info

    # Return all sensor history, plus latest
    # { 'sensor_history': [ ... ]
    #   'sensor_info': { ... }
    # }
    def db_lookup_sensor_history(self, acp_id):
        query = "SELECT record_id, acp_ts_end, sensor_info FROM sensors WHERE acp_id=%s ORDER BY acp_ts_end DESC"
        query_args = (acp_id,)

        try:
            return_info = {}
            rows = self.db_conn.dbread(query, query_args)
            if len(rows) == 0:
                return None
            sensor_history = []
            current_sensor_info = None
            for row in rows:
                ( record_id, acp_ts_end, sensor_info) = row
                sensor_info["acp_record_id"] = record_id # Embed the record_id
                if acp_ts_end is None:
                    current_sensor_info = sensor_info
                else:
                    sensor_history.append(sensor_info)
        except:
            print(sys.exc_info(),flush=True,file=sys.stderr)
            return None

        return { 'sensor_history': sensor_history, 'sensor_info': current_sensor_info }

    # Return metadata from DATABASE for a single sensor type
    def db_lookup_sensor_type(self, acp_type_id):

        query = "SELECT type_info FROM sensor_types WHERE acp_type_id=%s AND acp_ts_end IS NULL"
        query_args = (acp_type_id,)

        try:
            type_info = {}
            rows = self.db_conn.dbread(query, query_args)
            if len(rows) != 1:
                return None
            type_info = rows[0][0]

        except:
            print(sys.exc_info(),flush=True,file=sys.stderr)
            return None

        print(f'Updating SENSOR_TYPES[{acp_type_id}]')
        SENSOR_TYPES[acp_type_id] = type_info
        return type_info

    # Return all sensor type history, including latest, as list
    def db_lookup_sensor_type_history(self, acp_type_id):
        query = "SELECT record_id, type_info FROM sensor_types WHERE acp_type_id=%s ORDER BY acp_ts_end DESC"
        query_args = (acp_type_id,)

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

    # Lookup a sensor type (from the in-memory cache)
    def type_lookup(self, acp_type_id):
        global SENSOR_TYPES
        try:
            type_info = SENSOR_TYPES[acp_type_id]
        except:
            return None
        return type_info

    # Update a list_obj of objects with "acp_location_xyz" and "acp_boundary_xyz" properties
    #DEBUG this routine is common to api_bim and api_sensors so should be in acp_coordinates
    def add_xyzf(self, coordinate_system, list_obj):
        if list_obj is None:
            return

        for acp_id in list_obj:
            if "acp_location" not in list_obj[acp_id]:
                # We need acp_location to for the coordinate system
                continue # no acp_location in this object so skip
            obj = list_obj[acp_id]
            acp_location = obj["acp_location"]
            sensor_coordinate_system = acp_location["system"]
            if sensor_coordinate_system != coordinate_system:
                continue
            # Note the xyz coordinates may already be cached in the bim data
            if "acp_location_xyz" not in obj:
                obj["acp_location_xyz"] = self.coordinate_systems[coordinate_system].xyzf(acp_location)
            if "acp_boundary" in obj and "acp_boundary_xyz" not in obj:
                obj["acp_boundary_xyz"] = self.acp_boundary_to_xy(coordinate_system, obj["acp_boundary"])

        return

    #DEBUG this should be in acp_coordinates
    ####################################################################
    ### In-Building coordinate system -> XYZ coords                 ###
    ####################################################################

    # Convert the building coords boundaries into equivalent latlngs
    # acp_boundary is a list [{ boundary_type, boundary: [...] }...]
    def acp_boundary_to_xy(self, coordinate_system, acp_boundary):
        xy_boundaries = [] # this is the list we will return when completed
        for boundary_obj in acp_boundary:
            # create new gps_boundary object, with type set as original
            xy_boundary = { "boundary_type": boundary_obj["boundary_type"] }
            # add the latlng points to this object
            xy_boundary["boundary"] = self.points_to_xy(coordinate_system, boundary_obj["boundary"])
            # append this new object to the list
            xy_boundaries.append(xy_boundary)

        return xy_boundaries

    def points_to_xy(self, coordinate_system, points):
        xy_points = []
        for point in points:
            xy_point = self.point_to_xy(coordinate_system, point)
            xy_points.append(xy_point)

        return xy_points

    def point_to_xy(self, coordinate_system, point):
        return self.coordinate_systems[coordinate_system].xy(point)

    #https://en.wikipedia.org/wiki/Even-odd_rule
    def is_point_in_path(self,x: int, y: int, poly) -> bool:
        #Determine if the point is in the path.

        #Args:
        #  x -- The x coordinates of point.
        #  y -- The y coordinates of point.
        #  poly -- a list of tuples [(x, y), (x, y), ...]

        #Returns:
        #  True if the point is in the path.

        num = len(poly)
        i = 0
        j = num - 1
        c = False
        for i in range(num):
            if ((poly[i][1] > y) != (poly[j][1] > y)) and \
                    (x < poly[i][0] + (poly[j][0] - poly[i][0]) * (y - poly[i][1]) /
                                    (poly[j][1] - poly[i][1])):
                c = not c
            j = i
        return c

    def find_in_list(self,item_id, item_list):
        for x in item_list:
            if x['crate_id'] == item_id:
                print ("I found it!")
                return x

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

    def write_type_obj(self, id, json_info_obj, merge=False):
        self.write_obj(id, json_info_obj, table_name="sensor_types", id_name="acp_type_id", json_name="type_info", merge=merge)

    def write_obj(self, id, json_info_obj, table_name="sensors", id_name="acp_id", json_name="sensor_info", merge=False):

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