from flask import Flask, request, render_template,url_for, redirect, jsonify, make_response
from flask_cors import CORS, cross_origin
from os import listdir, path
import json
from collections import defaultdict
import sys
from datetime import datetime
import time

from classes.bim_data_api import BIMDataAPI

DEBUG = True

app = Flask(__name__)
CORS(app)

###################
# BIM API SHIM
###################

#####################################
#api/bim for BIM oriented (meta)data
#####################################

@app.route('/get/<crate_id>/', defaults={'children': 0})
@app.route('/get/<crate_id>/<children>/')
def get_route(crate_id,children):
    global data_api
    if str(children)=='all': #or type(children)!=int:
        children=999
    else:
        try:
            children=int(children)
        except:
            children=999
    response = make_response(data_api.get(crate_id, children), 200)
    response.mimetype = "application/json"
    return response

# get_floor_number/<coordinate_system>/<floor_number>/
# Returns BIM objects for floor EXCLUDING crate_type=="floor"
@app.route('/get_floor_number/<coordinate_system>/<floor_number>/')
def get_floor_number_route(coordinate_system,floor_number):
    global data_api
    response = make_response(data_api.get_floor_number(coordinate_system,floor_number), 200)
    response.mimetype = "application/json"
    return response

@app.route('/get_gps/<crate_id>/', defaults={'children': 0})
@app.route('/get_gps/<crate_id>/<children>/')
def get_gps_route(crate_id, children):
    global data_api
    response = make_response(data_api.get_gps(crate_id, children), 200)
    response.mimetype = "application/json"
    return response

@app.route('/get_xyzf/<crate_id>/', defaults={'children': 0})
@app.route('/get_xyzf/<crate_id>/<children>/')
def get_xyzf_route(crate_id, children):
    global data_api
    response = make_response(data_api.get_xyzf(crate_id, children), 200)
    response.mimetype = "application/json"
    return response

####################################################################
#
# Main
#
####################################################################

if __name__ == '__main__':
    print("BIM API starting...")

    with open('../settings.json', 'r') as settings_file:
        settings_data = settings_file.read()

    # parse file
    settings = json.loads(settings_data)

    print("BIM API loaded settings.json")

    data_api = BIMDataAPI(settings)

    print("Starting BIM API on {}:{}".format(settings["bim_host"],settings["bim_port"]))
    app.run( host=settings["bim_host"],
             port=settings["bim_port"],
             debug=DEBUG)
