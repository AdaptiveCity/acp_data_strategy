
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
# People DataAPI
#
###################################################################

PEOPLE=None
INSTS=None
GROUPS=None
BIM=None

class PeopleDataAPI(object):

    def __init__(self, settings):
        global PEOPLE
        global INSTS
        global GROUPS
        global BIM
        print("Initializing People DataAPI")
        self.settings = settings

        self.db_conn = DBConn(self.settings)

        PEOPLE = self.load_people()
        print("Loaded people table")

        INSTS = self.load_insts()
        print("Loaded insts table")

        GROUPS = self.load_groups()
        print("Loaded groups table")

        BIM = self.load_bim()
        print("Loaded bim table")

        # Import acp_coordinates Python modules for each coordinate system listed in settings.json.
        self.load_coordinate_systems()

    #####################################################################
    #  METHODS CALLED FROM API                                          #
    #####################################################################

    # Takes in person_id and returns the person's information
    def get(self, person_id, path):
        global PEOPLE

        if DEBUG:
            print("get {}".format(person_id), file=sys.stdout)

        # Read the person from the DATABASE, purely to refresh the in-memory cache (People)

        person_info = self.db_lookup_person(person_id)

        if person_info == None:
            return {'error': 'Person not present'}

        person_insts = self.retrieve_person_insts(person_info, path)
        person_bim = self.retrieve_person_bim(person_info, path)
        
        person_info['insts'] = person_insts
        person_info['bim'] = person_bim

        return person_info

    # Return a list of people's metadata
    # Maybe we should add "insts": { } for relevant inst metadata
    # Maybe we should add "groups": { } for relevant group metadata
    # Returns { "people": { } }
    def list(self, args):
        global PEOPLE
        # debug listing of querystring args
        if DEBUG:
            args_str = ""
            for key in args:
                args_str += key+"="+args.get(key)+" "
            print("list() {}".format(args_str) )
        # Set bool to include sensor type metadata
        include_inst_info = "inst_metadata" in args and args["inst_metadata"] == "true"
        include_group_info = "group_metadata" in args and args["group_metadata"] == "true"
        person_list_obj = {}
        inst_list_obj = {}
        group_list_obj = {}

        for person_id in PEOPLE:
            person = PEOPLE[person_id]

            if True:                   # Here's where we'd filter the results
                person_list_obj[person_id] = person
                if include_inst_info and "acp_type_id" in person:
                    acp_type_id = person["acp_type_id"]
                    inst_info = None #self.type_lookup(acp_type_id)
                    if info_info is not None:
                        inst_list_obj[acp_type_id] = type_info

        # Build return object { sensors: [..], types: [..]}
        return_obj = { 'people': person_list_obj }
        if include_inst_info:
            return_obj["insts"] = inst_list_obj

        return return_obj


    # Get the full history of metadata for a given person
    # This method will necessarily read the data from the database.
    def get_history(self, person_id):
        print(f"get_history {person_id}",file=sys.stderr, flush=True)
        global PEOPLE
        try:
            # returns { 'history': [  <list of sensor_info objects> ] }
            history = self.db_lookup_person_history(person_id)
        except:
            print(f"get_history() error person_id {person_id}",file=sys.stderr, flush=True)
            return {}
        return { 'history': history }

    # Updates metadata for person object <person_id>
    def update(self, person_id, person_metadata):
        if "person_id" not in person_metadata or person_id != person_metadata["person_id"]:
            print(f'update { person_id } wrong person_id in person_metadata',file=sys.stderr,flush=True)
            return f'{{ "acp_error": "api_person bad person_id {person_id} in person metadata" }}'

        try:
            self.write_obj(person_id, person_metadata)
        except:
            print(f'Error /update/{ person_id }/',file=sys.stderr,flush=True)
            print(f'{ json.dumps(person_metadata, indent=4) }', file=sys.stderr, flush=True)
            print( sys.exc_info() )
            return { "acp_error": "api_bim db write failed" }

        # Update in-memory entry
        PEOPLE[person_id] = person_metadata
        print(f'update { person_id } updated',file=sys.stderr,flush=True)
        return {}


    ###########################################################################
    #
    # Support functions
    #
    ###########################################################################

    # Load ALL the People data from the store
    def load_people(self):

        # To select *all* the latest people objects:
        query = "SELECT person_id, person_info FROM people WHERE acp_ts_end IS NULL"

        try:
            people_data = {}
            rows = self.db_conn.dbread(query, None)
            for row in rows:
                id, json_info = row
                people_data[id] = json_info

        except:
            print(sys.exc_info(),flush=True,file=sys.stderr)
            return {}

        return people_data

    # Load ALL the Insts data from store
    def load_insts(self):

        # To select *all* the latest inst objects
        query = "SELECT inst_id, inst_info FROM insts WHERE acp_ts_end IS NULL"

        try:
            insts_data = {}
            rows = self.db_conn.dbread(query, None)
            for row in rows:
                id, json_info = row
                insts_data[id] = json_info

        except:
            print(sys.exc_info(),flush=True,file=sys.stderr)
            return {}

        return insts_data

    # Load ALL the Groups data from store
    def load_groups(self):

        # To select *all* the latest group objects
        query = "SELECT group_id, group_info FROM groups WHERE acp_ts_end IS NULL"

        try:
            groups_data = {}
            rows = self.db_conn.dbread(query, None)
            for row in rows:
                id, json_info = row
                groups_data[id] = json_info

        except:
            print(sys.exc_info(),flush=True,file=sys.stderr)
            return {}

        return groups_data

    # Load ALL the BIM data from store
    def load_bim(self):

        # To select *all* the latest bim objects
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

    # Return metadata from DATABASE for a single person
    # and update entry in-memory cache (BIM_data).
    def db_lookup_person(self, person_id):
        global PEOPLE

        query = "SELECT person_info FROM people WHERE person_id=%s AND acp_ts_end IS NULL"
        query_args = (person_id,)

        try:
            person_info = {}
            rows = self.db_conn.dbread(query, query_args)
            if len(rows) != 1:
                return None
            person_info = rows[0][0]
        except:
            print(sys.exc_info(),flush=True,file=sys.stderr)
            return None

        # Refresh in-memory copy
        PEOPLE[person_id] = person_info

        return person_info

    # Return all history for a given person as list
    def db_lookup_person_history(self, person_id):
        query = "SELECT record_id, person_info FROM people WHERE person_id=%s ORDER BY acp_ts_end DESC"
        query_args = (person_id,)

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

    # Return all institutions in hierarchy
    def retrieve_person_insts(self, person_info, path):
        global INSTS
        person_insts = person_info['insts']

        if path:
            try:
                for inst in person_insts:
                    parents = []
                    if inst in INSTS.keys():
                        parent = INSTS[inst]['parent_insts'][0]
                        while parent != 'ROOT':
                            parents.append(parent)
                            parent = INSTS[parent]['parent_insts'][0]
                    person_insts[inst]['parents'] = parents
            except:
                print(sys.exc_info(),flush=True,file=sys.stderr)
                return []

        return person_insts

    # Return all bim objects in hierrachy
    def retrieve_person_bim(self, person_info, path):
        global BIM
        person_bim = person_info['bim']

        if path:
            for crate in person_bim:
                parent_crates = []
                parent = BIM[crate]['parent_crate_id']
                while parent not in self.settings['coordinate_systems'] and parent in BIM:
                    parent_crates.append(parent)
                    parent = BIM[parent]['parent_crate_id']
                parent_crates.append(parent)
                
                person_bim[crate]['parents'] = parent_crates

        return person_bim

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

    def write_obj(self, id, json_info_obj, table_name="people", id_name="person_id", json_name="person_info", merge=False):

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
