from flask import Flask, request, render_template, jsonify, redirect, flash, session, abort
from flask_cors import CORS, cross_origin
from os import listdir, path, urandom
import json
import requests as rq
from CONFIG import TABLE_ISM, ADMIN, ADMIN_PASSWORD
from dbconn import dbread
from translation import *
from read_metadata import *
from write_metadata import updateSensorMetadata
from InBuildingCoordinates import InBuildingCoordinates

app = Flask(__name__)
cors = CORS(app)

DEBUG = True

# Initializes all the inbuilding coordinate systems
def initialize_indoor_systems():
    sdict = {}

    query = "SELECT * from "+TABLE_ISM
    rows = dbread(query)
    for row in rows:
        iC = InBuildingCoordinates(row[0], row[1]['lat_origin'], row[1]['lng_origin'], row[1]['dlat'], row[1]['dlng'], row[1]['dx'], row[1]['dy'])
        sdict[row[0]] = iC

    return sdict

# Endpoint to provide access for updating sensor information in the database
@app.route('/sensors/admin')
def admin():
    if not session.get('logged_in'):
        return render_template('sensor_login.html')
    else:
        return render_template('sensors.html')

# Login
@app.route('/sensors/login', methods=['POST'])
def do_admin_login():
    if request.form['password'] == ADMIN_PASSWORD and request.form['username'] == ADMIN:
        session['logged_in'] = True
        return render_template('sensors.html')
    else:
        flash('wrong password!')
        return admin()

# Logout
@app.route("/sensors/logout")
def logout():
    session['logged_in'] = False
    return admin()

# Add/Update sensor based on user input.
@app.route('/sensors/addsensor', methods=['POST'])
def addsensor():
    status = False
    try:
        acp_id = (request.form['acp_id']).strip()
        stype = (request.form['type']).strip()
        source = (request.form['source']).strip()
        owner = (request.form['owner']).strip()
        features = (request.form['features']).strip()
        acp_location = (request.form['acp_location']).strip()
        new_elements = (request.form['new_element']).strip()
        status = updateSensorMetadata(acp_id, stype, source, owner, features, acp_location, new_elements)
    except KeyError:
        status = False
    if status:
        flash('Sensor Added')
    else:
        flash('Error while adding. Please check the inputs.')
    return admin()

# Return all available sources in ACP
@app.route('/api/sensors/sources')
def sources():
    sourceList = getSources()
    response = {}
    response['data'] = []
    for source in sourceList:
        response['data'].append({'source':source})
    json_response = json.dumps(response)
    return(json_response)

# Return all sensors for a given source. If source is null then return all sensors.
@app.route('/api/sensors')
def sensors():
    if DEBUG:
        print('Requested')
    print(request)
    source = request.args.get('source')

    sensorList = getSensors(source)

    response = {}
    response['data'] = []
    for sensor in sensorList:
        response['data'].append({'sensor':sensor})
    json_response = json.dumps(response)
    return(json_response)

# Return all data attributes for a given sensor
@app.route('/api/features')
def features():

    sensor = request.args.get('sensor')

    featureList = getFeatures(sensor)

    response = {}
    response['data'] = []
    for feature in featureList:
        response['data'].append({'feature':feature.strip()})
    json_response = json.dumps(response)
    return(json_response)

# Return all details for a given sensor
@app.route('/api/sensors/get/<acp_id>')
def get_sensor_metadata_route(acp_id):
 
    response = {}
    response['data'] = getSensorDetails(acp_id)

    json_response = json.dumps(response)
    return(json_response)

# Return all the sensors in a given crate in the bim module
@app.route('/api/sensors/get/bim/<crate_id>')
def get_sensors_loc_route(crate_id):
    sensorList = getSensorsInCrate(crate_id)
    response = {}
    response['data'] = []
    for sensor in sensorList:
        response['data'].append({'sensor':sensor})
    json_response = json.dumps(response)
    return(json_response)

# Return a count of all the sensors in the given crate_id. If children is 
# specified then count recurrsively to children level. If children is "all", 
# then provides details of sensors in all the children crates.
@app.route('/api/sensors/get_count/<crate_id>', defaults={'children': 0})
@app.route('/api/sensors/get_count/<crate_id>/<children>')
def get_sensors_count_route(crate_id, children):
    url = ""
    if children == 'all':
        url = "http://localhost:5000/api/bim/get/"+crate_id+"/all/"
    else:
        url = "http://localhost:5000/api/bim/get/"+crate_id+"/"+str(children)+"/"

    response = rq.get(url)

    count = getSensorCount(response.json())

    json_response = json.dumps(count)
    return(json_response)


systemsDict = initialize_indoor_systems()

app.secret_key = urandom(12)
app.run(port=5010,debug=DEBUG)