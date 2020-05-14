from flask import Flask, request, render_template, jsonify, redirect, flash, session, abort
from flask_cors import CORS, cross_origin
from os import listdir, path, urandom
import json
from collections import defaultdict
import sys
from datetime import datetime
from math import cos, radians
import psycopg2
from CONFIG import *

app = Flask(__name__)
cors = CORS(app)

DEBUG = True
TABLE_ISM = 'indoor_system_metadata'
TABLE_MD = 'metadata'

def initialize_indoor_systems():
    sdict = {}
    con = psycopg2.connect(database=PGDATABASE,
                            user=PGUSER,
                            password=PGPASSWORD,
                            host=PGHOST,
                            port=PGPORT)
    cur = con.cursor()
    cur.execute("SELECT * from "+TABLE_ISM)
    rows = cur.fetchall()

    for row in rows:
        iC = inbuildingCoord(row[0], row[1], row[2], row[3], row[4], row[5], row[6])
        sdict[row[0]] = iC

    return sdict

def getSources():

    query = "SELECT distinct info->'source' from "+TABLE_MD
    slist = []

    con = psycopg2.connect(database=PGDATABASE,
                            user=PGUSER,
                            password=PGPASSWORD,
                            host=PGHOST,
                            port=PGPORT)

    cur = con.cursor()
    cur.execute(query)
    rows = cur.fetchall()

    for row in rows:
        slist.append(row[0])

    return slist

def getSensors(source):

    query = ''
    slist = []

    if source == "":
        query = "SELECT acp_id from "+TABLE_MD
    else:
        query = "SELECT acp_id from "+TABLE_MD+ " WHERE info->>'source'='"+source+"'"

    con = psycopg2.connect(database=PGDATABASE,
                            user=PGUSER,
                            password=PGPASSWORD,
                            host=PGHOST,
                            port=PGPORT)

    cur = con.cursor()
    cur.execute(query)
    rows = cur.fetchall()

    for row in rows:
        slist.append(row[0])
    return slist

def getFeatures(sensor):

    query = ''
    slist = []

    query = "SELECT info->'features' from "+TABLE_MD+ " WHERE acp_id='"+sensor+"'"

    con = psycopg2.connect(database=PGDATABASE,
                            user=PGUSER,
                            password=PGPASSWORD,
                            host=PGHOST,
                            port=PGPORT)

    cur = con.cursor()
    cur.execute(query)
    rows = cur.fetchall()

    return rows[0][0].split(',')

def validateLocationInput(acp_location):
    validation = False
    try:
        jData = json.loads(acp_location)
        if jData['system'] == 'GPS':
            if isinstance(jData['acp_lat'], (float, int)) and isinstance(jData['acp_lng'], (float, int)) and isinstance(jData['acp_alt'], (float, int)):
                validation = True
        elif jData['system'] == 'WGB':
            if isinstance(jData['x'], (float, int)) and isinstance(jData['y'], (float, int)) and isinstance(jData['f'], (float, int)) and isinstance(jData['zf'], (float, int)):
                validation = True
        elif jData['system'] == "OLH":
            if 'crate_id' in jData and 'parent_crate_id' in jData and 'crate_type' in jData:
                validation = True
    except:
        if DEBUG:
            print(sys.exc_info())

    return validation


def updateMetadata(acp_id, type, source, owner, features, acp_location):
    acplocValidation = validateLocationInput(acp_location)
    if not acplocValidation:
        return False

    ftrList = features.split(',')
    ts = datetime.timestamp(datetime.now())
    data = {"ts":ts,"type":type, "source":source, "owner":owner, "features":features, "acp_location":json.loads(acp_location)}

    flag = False
    con = psycopg2.connect(database=PGDATABASE,
                            user=PGUSER,
                            password=PGPASSWORD,
                            host=PGHOST,
                            port=PGPORT)
    cur = con.cursor()

    query = "INSERT INTO " + TABLE_MD + " (acp_id, info) VALUES ('" + acp_id + "','" + json.dumps(data) + "')"
    try:
        cur.execute(query)
        flag = True
    except:
        if DEBUG:
            print(cur.query)
            print(sys.exc_info())

    con.commit()
    con.close()
    
    return flag


class inbuildingCoord:
    def __init__(self, system, lat_o, lng_o, dlat, dlng, dx, dy):
        self.system = system
        self.lat_o = float(lat_o)
        self.lng_o = float(lng_o)
        self.dlat = float(dlat)
        self.dlng = float(dlng)
        self.dx = float(dx)
        self.dy = float(dy)

    def getGPS(self, x, y, f, z):

        lat = self.lat_o + (y*self.dlat)/self.dy
        lng = self.lng_o + (x*cos(radians(lat))*self.dlng)/self.dx

        return lat, lng, f+z

    def getIndoor(self, lat, lng, alt):

        vs = self.dy/self.dlat
        hs = self.dx/(cos(radians(lat))*self.dlng)

        x = (lng - self.lng_o) * hs
        y = (lat - self.lat_o) * vs
        f, z = 0, 0
        if alt != 0:
            f = int(alt/10)
            z = round(((alt*alt)%alt)/alt,2)

        return x, y, f, z


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
        type = (request.form['type']).strip()
        source = (request.form['source']).strip()
        owner = (request.form['owner']).strip()
        features = (request.form['features']).strip()
        acp_location = (request.form['acp_location']).strip()
        status = updateMetadata(acp_id, type, source, owner, features, acp_location)
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

@app.route('/api/ctog')
def togps():
    system = request.args.get('system')
    x = float(request.args.get('x'))
    y = float(request.args.get('y'))
    f = float(request.args.get('f'))
    z = float(request.args.get('z'))

    lat, lng, alt = systemsDict[system].getGPS(x,y,f,z)

    response = {'lat':lat, 'lng':lng, 'alt':alt}
    json_response = json.dumps(response)
    return(json_response)

@app.route('/api/gtoc')
def toindoor():
    system = request.args.get('system')
    lat = float(request.args.get('lat'))
    lng = float(request.args.get('lng'))
    alt = float(request.args.get('alt'))

    x, y, f, z = systemsDict[system].getIndoor(lat, lng, alt)

    response = {'x':x, 'y':y, 'f':f, 'z':z}
    json_response = json.dumps(response)
    return(json_response)


systemsDict = initialize_indoor_systems()

app.secret_key = urandom(12)
app.run(port=5000,debug=DEBUG)
