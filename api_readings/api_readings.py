from flask import Flask, request, render_template,url_for, redirect, jsonify
from flask_cors import CORS, cross_origin
from os import listdir, path
import json
from collections import defaultdict
import sys
from datetime import datetime
import time

from classes.readings_data_api import ReadingsDataAPI

DEBUG = True

app = Flask(__name__)
CORS(app)

###################
# READINGS API SHIM
###################

#############################################
#api/readings for most recent sensor readings
#############################################

# /get/<acp_id>/?<args>
# The canonical "get" API call: /get/<acp_id>/[?metadata=true]
# Returns { "reading": <the latest sensor reading>,
#           "sensor_metadata": <sensors API data for this sensor> (optional)
#         }
# where:
#   /<acp_id>/ is the sensor identifier
#   ?metadata=true requests the sensor metadata to be included in the response
@app.route('/get/<acp_id>/')
def get_route(acp_id):
    global data_api
    return data_api.get(acp_id, request.args)

# /get_day/<acp_id>/[?date=YYYY-MM-DD][&metadata=true]
# Returns a day's-worth of readings for the required sensor.
# Defaults to 'today', or optional date can be given.
# Sensor metadata can also be returned as for /get/.
@app.route('/get_day/<acp_id>/')
def get_day_route(acp_id):
    global data_api
    return data_api.get_day(acp_id, request.args)

@app.route('/historicaldata/')
def history_data_route():
    global data_api
    return data_api.history_data(request.args)

#@app.route('/get/bim/<crate_id>')
#def get_sensor_readings_in_route(crate_id):#
#    global data_api
#    return data_api.get_sensor_readings_in(crate_id)

####################################################################
#
# Main
#
####################################################################

if __name__ == '__main__':
    print("READINGS API starting...")

    with open('../settings.json', 'r') as settings_file:
        settings_data = settings_file.read()

    # parse file
    settings = json.loads(settings_data)

    print("READINGS API loaded settings.json")

    data_api = ReadingsDataAPI(settings)

    print("Starting READINGS API on {}:{}".format(settings["readings_host"],settings["readings_port"]))
    app.run( host=settings["readings_host"],
             port=settings["readings_port"],
             debug=DEBUG)
