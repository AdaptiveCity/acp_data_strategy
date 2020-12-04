from flask import Flask, request, render_template,url_for, redirect, jsonify
from flask_cors import CORS, cross_origin
from os import listdir, path
import json
from collections import defaultdict
import sys
from datetime import datetime
import time

from classes.sensors_data_api import SensorsDataAPI

DEBUG = True

app = Flask(__name__)
CORS(app)


######################
# SENSORS POSTGRES API
######################

#########################################
#api/sensors for sensor oriented metedata
#########################################

# /get/<acp_id>/[?metadata=true] :
# The canonical "get" api call, returns the sensor metadata for sensor with id "<acp_id>".
# Given optional "?metadata=true", the API will also return the sensor *type* metadata.
@app.route('/get/<acp_id>/')
def get_route(acp_id):
    global data_api
    return data_api.get(acp_id)

# /get_history/<acp_id>/[?metadata=true] :
# Similar to above but returns entire history of sensor metadata for a given sensor.
# Sensor TYPE metadata is not returned (as it may have changed during history)
@app.route('/get_history/<acp_id>/')
def get_history_route(acp_id):
    global data_api
    return data_api.get_history(acp_id)

@app.route('/get_bim/<coordinate_system>/<crate_id>/')
def get_bim_route(coordinate_system, crate_id):
    global data_api
    return data_api.get_bim(coordinate_system, crate_id)

#DEBUG replaced with get_floor_number
#@app.route('/get_count/<crate_id>/', defaults={'children': 0})
#@app.route('/get_count/<crate_id>/<children>/')
#def get_count_route(crate_id, children):
#    global data_api
#
#    if str(children)=='all': #or type(children)!=int:
#        children=999
#    else:
#        try:
#            children=int(children)
#        except:
#            children=999
#    return data_api.get_sensors_count(crate_id, children)

# Return sensors found on a given floor
@app.route('/get_floor_number/<coordinate_system>/<floor_number>/')
def get_floor_number_route(coordinate_system, floor_number):
    global data_api
    return data_api.get_floor_number(coordinate_system, floor_number)

#DEBUG this API call **really** needs parameters (what info to show, lat/lng box?)
# Get all sensors with a GPS location (i.e. lat/lng)
@app.route('/get_gps/')
@cross_origin()
def get_gps_route():
    global data_api
    return data_api.get_gps()

#
@app.route('/get_type/<acp_type_id>/')
def get_type_route(acp_type_id):
    global data_api
    return data_api.get_type(acp_type_id)

# Return a list of sensors
# We could support querystring filters e.g.
# '?feature=temperature'
@app.route('/list/')
#@cross_origin()
def list_route():
    global data_api
    return data_api.list(request.args)

# Return a list of sensor types
# We could support querystring filters e.g.
# '?feature=temperature'
@app.route('/list_types/')
#@cross_origin()
def list_types_route():
    global data_api
    return data_api.list_types(request.args)

####################################################################
#
# Main
#
####################################################################

if __name__ == '__main__':
    print("SENSORS PostgreSQL API starting...")

    with open('../secrets/settings.json', 'r') as settings_file:
        settings_data = settings_file.read()

    # parse file
    settings = json.loads(settings_data)

    print("SENSORS API loaded settings.json")

    data_api = SensorsDataAPI(settings)

    print("Starting SENSORS API on {}:{}".format(settings["sensors_host"],settings["sensors_port"]))
    app.run( host=settings["sensors_host"],
             port=settings["sensors_port"],
             debug=DEBUG)
