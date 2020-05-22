from flask import Flask, request, render_template, jsonify, redirect, flash, session, abort
from flask_cors import CORS, cross_origin
from os import listdir, path, urandom
import json
from CONFIG import TABLE_ISM, ADMIN, ADMIN_PASSWORD
from dbconn import dbread
from translation import *
from read_metadata import *
from write_metadata import updateMetadata
from InBuildingCoordinates import InBuildingCoordinates

app = Flask(__name__)
cors = CORS(app)

DEBUG = True

def initialize_indoor_systems():
    sdict = {}

    query = "SELECT * from "+TABLE_ISM
    rows = dbread(query)
    for row in rows:
        iC = InBuildingCoordinates(row[0], row[1], row[2], row[3], row[4], row[5], row[6])
        sdict[row[0]] = iC

    return sdict

@app.route('/admin')
def admin():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        return render_template('admin.html')

@app.route('/login', methods=['POST'])
def do_admin_login():
    if request.form['password'] == ADMIN_PASSWORD and request.form['username'] == ADMIN:
        session['logged_in'] = True
        return render_template('admin.html')
    else:
        flash('wrong password!')
        return admin()

@app.route("/logout")
def logout():
    session['logged_in'] = False
    return admin()


@app.route('/addsensor', methods=['POST'])
def addsensor():
    status = False
    try:
        acp_id = (request.form['acp_id']).strip()
        stype = (request.form['type']).strip()
        source = (request.form['source']).strip()
        owner = (request.form['owner']).strip()
        features = (request.form['features']).strip()
        acp_location = (request.form['acp_location']).strip()
        status = updateMetadata(acp_id, stype, source, owner, features, acp_location)
    except KeyError:
        status = False
    if status:
        flash('Sensor Added')
    else:
        flash('Error while adding. Please check the inputs.')
    return admin()

@app.route('/api/sources')
def sources():
    sourceList = getSources()
    response = {}
    response['data'] = []
    for source in sourceList:
        response['data'].append({'source':source})
    json_response = json.dumps(response)
    return(json_response)

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

@app.route('/api/itog')
def itogps():
    system = request.args.get('system')
    x = float(request.args.get('x'))
    y = float(request.args.get('y'))
    f = float(request.args.get('f'))
    z = float(request.args.get('zf'))

    lat, lng, alt = systemsDict[system].getGPS(x,y,f,z)

    response = {'lat':lat, 'lng':lng, 'alt':alt}
    json_response = json.dumps(response)
    return(json_response)

@app.route('/api/gtoi')
def gtoindoor():
    system = request.args.get('system')
    lat = float(request.args.get('lat'))
    lng = float(request.args.get('lng'))
    alt = float(request.args.get('alt'))

    x, y, f, z = systemsDict[system].getIndoor(lat, lng, alt)

    response = {'x':x, 'y':y, 'f':f, 'zf':z}
    json_response = json.dumps(response)
    return(json_response)

@app.route('/api/itoo')
def itoolh():
    system = request.args.get('system')
    x = float(request.args.get('x'))
    y = float(request.args.get('y'))
    f = float(request.args.get('f'))

    floor_id = floors[system][int(f)]

    crates = get_all_crates(floor_id)
    crate_id = get_crate(crates, x, y)
    
    response = {}

    if crate_id == '':
        response = {'crate_id':floors[system][int(f)], 'parent_crate_id':system, 'crate_type':'floor'}
    else:
        response = {'crate_id':crate_id, 'parent_crate_id':floors[system][int(f)], 'crate_type':'room'}
                
    json_response = json.dumps(response)
    return(json_response)

@app.route('/api/otoi')
def otoindoor():
    system = request.args.get('system')
    crate_id = request.args.get('crate_id')
    x, y = getXY(crate_id)
    f = getCrateFloor(system, crate_id)

    response = {'system':system, 'x':x, 'y':y, 'f':f, 'z':0}

    json_response = json.dumps(response)
    return(json_response)


systemsDict = initialize_indoor_systems()

app.secret_key = urandom(12)
app.run(port=5000,debug=DEBUG)