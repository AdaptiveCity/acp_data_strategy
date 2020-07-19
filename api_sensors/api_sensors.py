from flask import Flask, request, render_template,url_for, redirect, jsonify
from flask_cors import CORS, cross_origin
from os import listdir, path
import json
from collections import defaultdict
import sys
from datetime import datetime
import time

from classes.sensors_data_api import DataAPI

DEBUG = True

app = Flask(__name__)
CORS(app)


###################
# SENSORS API SHIM
###################

#########################################
#api/sensors for sensor oriented metedata
#########################################

@app.route('/get/<acp_id>/')
def get_route(acp_id):
    global data_api
    return data_api.get_sensor_metadata(acp_id)

@app.route('/get_bim/<crate_id>/')
def get_bim_route(crate_id):
    global data_api
    return data_api.get_bim(crate_id)

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
@app.route('/get_gps')
@cross_origin()
def get_gps_route():
    global data_api
    return data_api.get_gps()

####################################################################
#
# Main
#
####################################################################

if __name__ == '__main__':
    print("SENSORS API starting...")

    with open('../settings.json', 'r') as settings_file:
        settings_data = settings_file.read()

    # parse file
    settings = json.loads(settings_data)

    print("SENSORS API loaded settings.json")

    data_api = DataAPI(settings)

    print("Starting SENSORS API on {}:{}".format(settings["sensors_host"],settings["sensors_port"]))
    app.run( host=settings["sensors_host"],
             port=settings["sensors_port"],
             debug=DEBUG)
