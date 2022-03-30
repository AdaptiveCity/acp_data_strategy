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
from classes.decision_points import DecisionPoints

DEBUG = True

###################################################################
#
# READINGS DataAPI
#
###################################################################

#r = requests.get('https://api.github.com/repos/psf/requests')
#r.json()["description"]

class PermissionsEngine(object):

    PERMISSIONS=None

    def __init__(self, settings):
        global PERMISSIONS
        print("Initializing Permissions DataAPI")
        self.settings = settings

        # Establish connection to PostgreSQL
        self.db_conn = DBConn(self.settings)
        PERMISSIONS = self.load_permissions()

        self.basePath = self.settings['readings_base_path']

    # Check if the subject has access to the resource. The access_request format is as follows:
    # {
    #     "subject": {
    #         "subject_id": "rv355",
    #         "subject_type": "people"
    #     },
    #     "resource": {
    #         "resource_id": "elsys-co2-041bab",
    #         "resource_type": "sensors"
    #     },
    #     "action": ["R"]
    # }
    def check_abac(self, access_request):
        response_obj = {}
        
        response_obj = self.get_access_permission(access_request)

        json_response = json.dumps(response_obj)
        response = make_response(json_response)
        response.headers['Content-Type'] = 'application/json'
        return response

    def get_access_permission(self, access_request):
        permission_obj = {'permission': False}
        permission_order = self.settings['permission_order']

        for permission_id in permission_order:
            decision_point = getattr(DecisionPoints, PERMISSIONS[permission_id]['permission_info']['decision_point'])
            access = decision_point(DecisionPoints, self.settings, access_request, PERMISSIONS[permission_id]['permission_info'])
            if access == True:
                permission_obj['permission'] = True
                break
        return permission_obj


    ###########################################################################
    #
    # Support functions
    #
    ###########################################################################

    # Load ALL the Permissions data from the store (Not used currently)
    def load_permissions(self):

        # To select *all* the latest sensor objects:
        query = "SELECT permission_id, permission_info FROM permissions WHERE acp_ts_end IS NULL"

        try:
            permissions = {}
            rows = self.db_conn.dbread(query, None)
            for row in rows:
                id, json_info = row
                permissions[id] = json_info

        except:
            print(sys.exc_info(),flush=True,file=sys.stderr)
            return {}

        return permissions