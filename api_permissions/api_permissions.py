from flask import Flask, request, render_template,url_for, redirect, jsonify, make_response
from flask_cors import CORS, cross_origin
from os import listdir, path
import json
from collections import defaultdict
import sys
from datetime import datetime
import time

from classes.permissions_api import PermissionsAPI

DEBUG = True

app = Flask(__name__)
CORS(app)

#####################################
#api/people for People oriented (meta)data
#####################################

@app.route('/get/<person_id>/<object_id>/<object_type>/<operation_type>')
def get_route(person_id, object_id, object_type, operation_type):
    global permission_api

    response = make_response(permission_api.get(person_id, object_id, object_type, operation_type, request.args), 200)
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

    permission_api = PermissionsAPI(settings)

    print("Starting Permissions API on {}:{}".format(settings["permissions_host"],settings["permissions_port"]))
    app.run( host=settings["permissions_host"],
             port=settings["permissions_port"],
             debug=DEBUG)
