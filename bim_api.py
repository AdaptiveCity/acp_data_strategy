from flask import Flask, request, render_template, jsonify, redirect, flash, session, abort
from flask_cors import CORS, cross_origin
from os import listdir, path, urandom
import json
from CONFIG import TABLE_ISM, ADMIN, ADMIN_PASSWORD
from dbconn import dbread
from translation import *
from read_metadata import *
from write_metadata import updateBimMetadata
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
@app.route('/bim/admin')
def admin():
    if not session.get('logged_in'):
        return render_template('bim_login.html')
    else:
        return render_template('bim.html')

# Login
@app.route('/bim/login', methods=['POST'])
def do_admin_login():
    if request.form['password'] == ADMIN_PASSWORD and request.form['username'] == ADMIN:
        session['logged_in'] = True
        return render_template('bim.html')
    else:
        flash('wrong password!')
        return admin()

# Logout
@app.route("/bim/logout")
def logout():
    session['logged_in'] = False
    return admin()

# Add/Update bim information
@app.route('/bim/addcrate', methods=['POST'])
def addbim():
    status = False
    try:
        crate_id = (request.form['crate_id']).strip()
        parent_crate_id = (request.form['parent_crate_id']).strip()
        long_name = (request.form['long_name']).strip()
        ctype = (request.form['crate_type']).strip()
        description = (request.form['description']).strip()
        acp_boundary = (request.form['acp_boundary']).strip()
        acp_location = (request.form['acp_location']).strip()
        new_elements = (request.form['new_element']).strip()
        status = updateBimMetadata(crate_id, parent_crate_id, long_name, ctype, description, acp_boundary, acp_location, new_elements)
    except KeyError:
        status = False
    if status:
        flash('Crate Added')
    else:
        flash('Error while adding. Please check the inputs.')
    return admin()

# Return all the details of the specified crate_id. If children is specified,
# then return details of the given crate_id and the child crates down to level
# children. If children is "all", then provides details of all the children crates.
@app.route('/api/bim/get/<crate_id>/', defaults={'children': 0})
@app.route('/api/bim/get/<crate_id>/<children>/')
def get_bim_tree_route(crate_id,children):
    crateList = []
    if str(children) == 'all':
        crateList = getCrateDetails(crate_id)
    else:
        crateList = getCrateDetails(crate_id, int(children))

    response = {}
    response['data'] = []
    for crate in crateList:
        response['data'].append({'crate':crate})
    json_response = json.dumps(response)
    return(json_response)

# Get all the crates on a given floor in the specified system.
@app.route('/api/bim/get_floor_number/<system>/<floor_number>')
def get_floor_by_floor_number(system,floor_number):
    crateList = getCratesOnFloor(system, floor_number)

    response = {}
    response['data'] = []
    for crate in crateList:
        response['data'].append({'crate_id':crate})
    json_response = json.dumps(response)
    return(json_response)

# Translate from inbuilding coordinate system to global coordinate system
@app.route('/api/bim/itog')
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

# Translate from global coordinate system to inbuilding coordinate system
@app.route('/api/bim/gtoi')
def gtoindoor():
    system = request.args.get('system')
    lat = float(request.args.get('lat'))
    lng = float(request.args.get('lng'))
    alt = float(request.args.get('alt'))

    x, y, f, z = systemsDict[system].getIndoor(lat, lng, alt)

    response = {'x':x, 'y':y, 'f':f, 'zf':z}
    json_response = json.dumps(response)
    return(json_response)

# Translate from inbuilding coordinate system to object level hierarchy system
@app.route('/api/bim/itoo')
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

# Translate from object level hierarchy to inbuilding coordinates
@app.route('/api/bim/otoi')
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