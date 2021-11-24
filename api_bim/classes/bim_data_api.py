
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
# BIM DataAPI
#
###################################################################

BIM=None

class BIMDataAPI(object):

    def __init__(self, settings):
        global BIM
        print("Initializing BIM DataAPI")
        self.settings = settings

        self.db_conn = DBConn(self.settings)

        BIM = self.load_BIM()
        print("Loaded bim table")

        self.load_coordinate_systems()

    #####################################################################
    #  METHODS CALLED FROM API                                          #
    #####################################################################

    # Takes in crate_id and depth and returns all children (default 0) of that crate
    # Note this /get/ API call returns a DICTIONARY indexed with crate_id,
    # even for a single BIM object.
    def get(self, crate_id, depth, path):
        global BIM

        if DEBUG:
            print("get {} {}".format(crate_id,depth), file=sys.stdout)

        # Read the crate from the DATABASE, purely to refresh the in-memory cache (BIM)
        crate = self.db_lookup_crate(crate_id)

        # Get list  of children of the desired crate to required depth
        crates_list = self.get_tree_list(crate_id, int(depth))

        if crates_list is None:
            return {}

        if path == True:
            crates = self.get_crate_path(crates_list)
        else:
            crates = self.clear_crate_path(crates_list)

        # Convert crates list [..] into list obj { "FE11": { ..}, .. }
        return self.list_to_dict("crate_id",crates)

    # Get the full history of metadata for a given crate (e.g. 'FE11')
    # This method will necessarily read the data from the database (as the BIM dictionary only
    # contains the latest metadata record not the prior history).
    def get_history(self, crate_id):
        print(f"get_history {crate_id}",file=sys.stderr, flush=True)
        global BIM
        try:
            # returns { 'history': [  <list of sensor_info objects> ] }
            history = self.db_lookup_crate_history(crate_id)
        except:
            print(f"get_history() error crate_id {crate_id}",file=sys.stderr, flush=True)
            return {}
        return { 'history': history }


    #takes in floor number and returns all room/corridor crates that have acp_location[f]==floor
    def get_floor_number(self, coordinate_system,floor_number):
        global BIM

        crates_dict = {}
        # coords.f(acp_location) will return floor number
        coords = self.coordinate_systems[coordinate_system]

        #get all WGB children (we retrieve all building children because some children can be spanning several floors)
        for crate_id in BIM:
            crate = BIM[crate_id]
            if "acp_location" in crate:
                loc = crate["acp_location"]
                if loc["system"] == coordinate_system and coords.f(loc) == int(floor_number):
                    crates_dict[crate_id] = crate

        self.add_xyzf(crates_dict)

        return crates_dict

    # Return the BIM object with additional properties (if they don't already exist):
    #     acp_lat, acp_lng, acp_alt
    #     acp_boundary_gps with x,y coordinates as
    #DEBUG api_bim.py get_gps depth not implemented - maybe we don't need it
    def get_gps(self, crate_id, depth):
        if crate_id not in BIM:
            return {}
        crate = BIM[crate_id]
        if "acp_location" not in crate:
            # We need acp_location to for the coordinate system
            return {}
        coordinate_system = crate["acp_location"]["system"]
        if "acp_boundary" in crate and "acp_boundary_gps" not in crate:
            crate["acp_boundary_gps"] = self.acp_boundary_to_gps(coordinate_system, crate["acp_boundary"])
        #DEBUG api_bim.py get_gps not implemented acp_lat, acp_lng, acp_alt
        crate_dict = {}
        crate_dict[crate_id] = crate
        return crate_dict

    # Return the BIM object with additional properties (if they don't already exist):
    #     acp_boundary_xyz with x,y coordinates in anticlockwise, meters units
    #DEBUG api_bim.py get_gps depth not implemented yet
    def get_xyzf(self, crate_id, depth):
        # Get list  of children of the desired crate to required depth
        crates_list = self.get_tree_list(crate_id, int(depth))

        crates_dict = self.list_to_dict("crate_id", crates_list)

        if DEBUG:
            print("get_xyzf {}".format(crates_dict))

        self.add_xyzf(crates_dict)

        if crates_dict is None:
            return {}

        return crates_dict

    # Updates metadata for bim object <crate_id>
    def update(self, crate_id, bim_metadata):
        if "crate_id" not in bim_metadata or crate_id != bim_metadata["crate_id"]:
            print(f'update { crate_id } wrong crate_id in bim_metadata',file=sys.stderr,flush=True)
            return f'{{ "acp_error": "api_bim bad crate_id {crate_id} in BIM metadata" }}'

        try:
            self.write_obj(crate_id, bim_metadata)
        except:
            print(f'Error /update/{ crate_id }/',file=sys.stderr,flush=True)
            print(f'{ json.dumps(bim_metadata, indent=4) }', file=sys.stderr, flush=True)
            print( sys.exc_info() )
            return { "acp_error": "api_bim db write failed" }

        # Update in-memory entry
        BIM[crate_id] = bim_metadata
        print(f'update { crate_id } updated',file=sys.stderr,flush=True)
        return {}


    ###########################################################################
    #
    # Support functions
    #
    ###########################################################################

    # Load ALL the BIM data from the store (usually data/BIM.json)
    def load_BIM(self):

        # To select *all* the latest sensor objects:
        query = "SELECT crate_id, crate_info FROM bim WHERE acp_ts_end IS NULL"

        try:
            BIM_data = {}
            rows = self.db_conn.dbread(query, None)
            for row in rows:
                id, json_info = row
                BIM_data[id] = json_info

        except:
            print(sys.exc_info(),flush=True,file=sys.stderr)
            return {}

        return BIM_data

    # Return metadata from DATABASE for a single sensor
    # and update entry in-memory cache (BIM_data).
    def db_lookup_crate(self, crate_id):
        global BIM

        query = "SELECT crate_info FROM bim WHERE crate_id=%s AND acp_ts_end IS NULL"
        query_args = (crate_id,)

        try:
            crate_info = {}
            rows = self.db_conn.dbread(query, query_args)
            if len(rows) != 1:
                return None
            crate_info = rows[0][0]
        except:
            print(sys.exc_info(),flush=True,file=sys.stderr)
            return None

        # Refresh in-memory copy
        BIM[crate_id] = crate_info

        return crate_info

    # Return all history for a given crate as list
    def db_lookup_crate_history(self, crate_id):
        query = "SELECT record_id, crate_info FROM bim WHERE crate_id=%s ORDER BY acp_ts_end DESC"
        query_args = (crate_id,)

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


    # Update a dictionary of creates with "acp_location_xyz" and "acp_boundary_xyz" properties
    def add_xyzf(self, crates):
        if crates is None:
            return

        for crate_id in crates:
            crate = crates[crate_id]
            if "acp_location" not in crate:
                # We need acp_location to for the coordinate system
                return # exit with crates unchanged
            acp_location = crate["acp_location"]
            coordinate_system = acp_location["system"]
            # Note the xyz coordinates may already be cached in the bim data
            if "acp_location_xyz" not in crate:
                crate["acp_location_xyz"] = self.coordinate_systems[coordinate_system].xyzf(acp_location)
            if "acp_boundary" in crate and "acp_boundary_xyz" not in crate:
                crate["acp_boundary_xyz"] = self.acp_boundary_to_xy(coordinate_system, crate["acp_boundary"])

        return

    #Compares crate_id with parent_id and determines if it's a match
    #is_child(POTENTIAL_CHILD, PARENT)
    def is_child(self, child,  parent_crate_id):
        child_id  = child['crate_id']
        parent_id = child['parent_crate_id']

        result = parent_id == parent_crate_id

        return result

    def get_crate_path(self, crate_list):
        updated_crate_list = []
        for crate in crate_list:
            parent_list = []
            parent = BIM[crate['crate_id']]['parent_crate_id']
            while parent not in self.settings['coordinate_systems'] and parent in BIM:
                parent_list.append(parent)
                parent = BIM[parent]['parent_crate_id']
            parent_list.append(parent)
            crate['parent_crate_path'] = parent_list
            updated_crate_list.append(crate)
        return updated_crate_list

    def clear_crate_path(self, crate_list):
        for crate in crate_list:
            if 'parent_crate_path' in crate.keys():
                del crate['parent_crate_path']
        return crate_list
            
    # return a list of immediate children of this crate
    def get_children(self, parent_id):
        #iterate through the BIM and determine if parent
        #has any children
        children = []
        for crate_id in BIM:
            crate = BIM[crate_id]
            if (self.is_child(crate, parent_id)):
                if DEBUG:
                    print("get_children adding child: {}".format(crate_id))
                children += [ crate ]

        return children

    # Return list of crates by flattening tree from crate_id down
    def get_tree_list(self, crate_id, depth):

        if DEBUG:
            print("get_tree",depth,crate_id)

        try:
            crate_list = [ BIM[crate_id] ]
        except KeyError:
            return []

        if depth > 0:
            children = self.get_children(crate_id) # returns list of immediate-child crate objects

            remaining_depth = depth - 1

            for child in children:
                # recursion
                crate_list += self.get_tree_list(child["crate_id"], remaining_depth)

        return crate_list

    ####################################################################
    ### In-Building coordinate system -> GPS coords                 ###
    ####################################################################

    # Convert the building coords boundaries into equivalent latlngs
    # acp_boundary is a list [{ boundary_type, boundary: [...] }...]
    def acp_boundary_to_gps(self, coordinate_system, acp_boundary):
        gps_boundaries = [] # this is the list we will return when completed
        for boundary_obj in acp_boundary:
            # create new gps_boundary object, with type set as original
            gps_boundary = { "boundary_type": boundary_obj["boundary_type"] }
            # add the latlng points to this object
            gps_boundary["boundary"] = self.points_to_gps(coordinate_system, boundary_obj["boundary"])
            # append this new object to the list
            gps_boundaries.append(gps_boundary)

        return gps_boundaries

    def points_to_gps(self, coordinate_system, points):
        gps_points = []
        for point in points:
            gps_point = self.point_to_gps(coordinate_system, point)
            gps_points.append(gps_point)

        return gps_points

    def point_to_gps(self, coordinate_system, point):
        return self.coordinate_systems[coordinate_system].latlng(point)

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

    # Convert a list of objs into a dictionary
    def list_to_dict(self, key_name, list):
        return_obj = {}
        # iterate the list objects
        for list_obj in list:
            # for each list object, add it as a dictionary entry
            return_obj[list_obj[key_name]] = list_obj
        return return_obj

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

    def write_obj(self, id, json_info_obj, table_name="bim", id_name="crate_id", json_name="crate_info", merge=False):

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
