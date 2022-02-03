from flask import Flask, request, render_template,url_for, redirect, jsonify, make_response
from flask_cors import CORS, cross_origin
from os import listdir, path
import json
from collections import defaultdict
import sys
from datetime import datetime
import time

from classes.permissions_engine import PermissionsEngine

DEBUG = True

app = Flask(__name__)
CORS(app)

#####################################
#api/people for People oriented (meta)data
#####################################

@app.route('/get_permission/<person_id>/<object_id>/<object_type>/<operation_type>')
def get_route(person_id, object_id, object_type, operation_type):
    global permission_api

    action = 'NA'
    if operation_type == 'read':
        action = 'R'
    elif operation_type == 'write':
        action = 'U'
    elif operation_type == 'add':
        action = 'C'
    elif operation_type == 'delete':
        action = 'D'

    access_request = {
        "subject": {
            "subject_id": 'crsid-'+person_id,
            "subject_type": "people"
        },
        "resource": {
            "resource_id": object_id,
            "resource_type": object_type
        },
        "action": action
    }

    response = make_response(permission_api.check_abac(access_request), 200)
    response.mimetype = "application/json"
    return response

@app.route('/get_admin/<person_id>/')
def get_admin_route(person_id):
    global permission_api

    response = make_response(permission_api.get_admin(person_id, request.args), 200)
    response.mimetype = "application/json"
    return response



####################################################################
#
# Main
#
####################################################################

if __name__ == '__main__':
    print("Permissions API starting...")

    with open('../secrets/settings.json', 'r') as settings_file:
        settings_data = settings_file.read()

    # parse file
    settings = json.loads(settings_data)

    print("Permission API loaded settings.json")

    with open('../secrets/permission_rules.json', 'r') as permission_file:
        permission_data = permission_file.read()

    # parse file
    permissions = json.loads(permission_data)

    print("Permission API loaded permission_rules.json")

    permission_api = PermissionsEngine(settings, permissions)

    print("Starting Permissions API on {}:{}".format(settings["permissions_host"],settings["permissions_port"]))
    app.run( host=settings["permissions_host"],
             port=settings["permissions_port"],
             debug=DEBUG)
