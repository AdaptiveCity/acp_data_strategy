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

DEBUG = True

###################################################################
#
# READINGS DataAPI
#
###################################################################

#r = requests.get('https://api.github.com/repos/psf/requests')
#r.json()["description"]

class PermissionsAPI(object):

    def __init__(self, settings):
        print("Initializing Permissions DataAPI")
        self.settings = settings
        self.basePath = self.settings['readings_base_path']

    def get(self, person_id, object_id, object_type, operation_type, args):
        response_obj = {}

        if object_type == 'sensors':
            response_obj = self.get_sensor_permissions(person_id, object_id, operation_type, args)
        elif object_type == 'bim':
            response_obj = self.get_bim_permissions(person_id, object_id, operation_type, args)
        elif object_type == 'readings':
            response_obj = self.get_reading_permissions(person_id, object_id, operation_type, args)
        elif object_type == 'people':
            response_obj = self.get_people_permissions(person_id, object_id, operation_type, args)
        else:
            response_obj["acp_error_id"] = "OBJECT_TYPE_ERROR"
            response_obj["acp_error_msg"] = "Object "+object_type+ "is not a valid object type."

        json_response = json.dumps(response_obj)
        response = make_response(json_response)
        response.headers['Content-Type'] = 'application/json'
        return response

    def get_sensor_permissions(self, person_id, object_id, operation_type, args):
        permission_obj = {}

        sensors_api_url = self.settings["API_SENSORS"]+'get/'+object_id+"/"
        #fetch data from Sensors api
        try:
            response = requests.get(sensors_api_url)
            response.raise_for_status()
            # access JSON content
            sensor_info = response.json()
        except HTTPError as http_err:
            print(f'get_sensor_info() HTTP GET error occurred: {http_err}')
            return { "acp_error_msg": "readings_data_api: get_sensor_info() HTTP error." }
        except Exception as err:
            print(f'get_sensor_info() Other GET error occurred: {err}')
            return { "acp_error_msg": "readings_data_api: Exception in get_sensor_info()."}

        
        people_api_url = self.settings["API_PEOPLE"]+'get/crsid-'+person_id+"/"
        #fetch data from People api
        try:
            response = requests.get(people_api_url)
            response.raise_for_status()
            # access JSON content
            people_info = response.json()
        except HTTPError as http_err:
            print(f'get_sensor_info() HTTP GET error occurred: {http_err}')
            return { "acp_error_msg": "readings_data_api: get_sensor_info() HTTP error." }
        except Exception as err:
            print(f'get_sensor_info() Other GET error occurred: {err}')
            return { "acp_error_msg": "readings_data_api: Exception in get_sensor_info()."}

        if 'crate_id' not in sensor_info:
            permission_obj['permission'] = True
            return permission_obj
            
        if sensor_info['crate_id'] in list(people_info['bim']['occupies_crates'].keys()):
            permission_obj['permission'] = True
        else:
            bim_api_url = self.settings["API_BIM"]+'get/'+sensor_info['crate_id']+"/?path=true"
            #fetch data from People api
            try:
                response = requests.get(bim_api_url)
                response.raise_for_status()
                # access JSON content
                bim_info = response.json()
            except HTTPError as http_err:
                print(f'get_sensor_info() HTTP GET error occurred: {http_err}')
                return { "acp_error_msg": "readings_data_api: get_sensor_info() HTTP error." }
            except Exception as err:
                print(f'get_sensor_info() Other GET error occurred: {err}')
                return { "acp_error_msg": "readings_data_api: Exception in get_sensor_info()."}

            if bim_info == {}:
                permission_obj['permission'] = True
                return permission_obj
                
            parent_crates = bim_info[sensor_info['crate_id']]['parent_crate_path']
            person_crates = list(people_info['bim']['occupies_crates'].keys())

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