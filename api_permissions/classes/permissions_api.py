"use strict"

from os import listdir, path
import json
from collections import defaultdict
import sys
from datetime import datetime
import time
from flask import request, make_response
from pathlib import Path

import requests
from requests.models import HTTPError
from classes.dbconn import DBConn

DEBUG = True

###################################################################
#
# READINGS DataAPI
#
###################################################################

#r = requests.get('https://api.github.com/repos/psf/requests')
#r.json()["description"]

class PermissionsAPI(object):

    SENSORS = None
    PEOPLE = None
    BIM = None

    def __init__(self, settings):
        print("Initializing Permissions DataAPI")
        global SENSORS, PEOPLE, BIM
        self.settings = settings

        # Establish connection to PostgreSQL
        self.db_conn = DBConn(self.settings)

        SENSORS = self.load_sensors()
        PEOPLE = self.load_people()
        BIM = self.load_BIM()
        self.basePath = self.settings['readings_base_path']

    def check_abac(self, access_request):
        response_obj = {}



        json_response = json.dumps(response_obj)
        response = make_response(json_response)
        response.headers['Content-Type'] = 'application/json'
        return response

    def get_admin(self, person_id, args):
        permission_obj = {}

        person_info = PEOPLE['crsid-'+person_id]

        try:
            if self.settings['admin_group_id'] in person_info['groups']:
                permission_obj['permission'] = True
            else:
                permission_obj['permission'] = False
        except KeyError:
            permission_obj['permission'] = False

        return permission_obj

    def get_sensor_permissions(self, person_id, object_id, operation_type, args):
        permission_obj = {}

        sensor_info = SENSORS[object_id]
        person_info = PEOPLE['crsid-'+person_id]        

        if 'crate_id' not in sensor_info:
            permission_obj['permission'] = True
            return permission_obj
            
        if sensor_info['crate_id'] in list(person_info['bim'].keys()):
            permission_obj['permission'] = True
        else:
            try:
                bim_info = BIM[sensor_info['crate_id']]
            except KeyError:
                permission_obj['permission'] = True
                return permission_obj

            if bim_info == {}:
                permission_obj['permission'] = True
                return permission_obj
                
            parent_crates = bim_info['parent_crate_path']
            person_crates = list(person_info['bim'].keys())

            crate_flag = False
            for crate in parent_crates:
                if crate in person_crates:
                    permission_obj['permission'] = True
                    crate_flag = True
                    break
            
            if not crate_flag:
                permission_obj["permission"] = False

        
        return permission_obj

    def get_bim_permissions(self, person_id, object_id, operation_type, args):
        return {"permission": True}

    def get_reading_permissions(self, person_id, object_id, operation_type, args):
        return {"permission": True}

    def get_people_permissions(self, person_id, object_id, operation_type, args):
        return {"permission": True}


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

        updated_BIM_data = {}
        for crate_id in BIM_data:
            crate = BIM_data[crate_id]
            parent_list = []
            parent = BIM_data[crate['crate_id']]['parent_crate_id']
            while parent not in self.settings['coordinate_systems'] and parent in BIM_data:
                parent_list.append(parent)
                parent = BIM_data[parent]['parent_crate_id']
            parent_list.append(parent)
            crate['parent_crate_path'] = parent_list
            updated_BIM_data.update({crate_id:crate})

        return updated_BIM_data


    def load_sensors(self):
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

    def load_people(self):
        # To select *all* the latest sensor objects:
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