from flask import Flask, request, render_template, jsonify
from os import listdir, path
import json
from collections import defaultdict
import sys
from datetime import datetime
from math import cos, radians
import psycopg2
from CONFIG import *

app = Flask(__name__)
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

    query = "SELECT info->'features from "+TABLE_MD+ " WHERE acp_id='"+sensor+"'"

    con = psycopg2.connect(database=PGDATABASE,
                            user=PGUSER,
                            password=PGPASSWORD,
                            host=PGHOST,
                            port=PGPORT)

    cur = con.cursor()
    cur.execute(query)
    rows = cur.fetchall()

    return rows[0][0]

class inbuildingCoord:
    def __init__(self, system, lat_o, lng_o, dlat, dlng, dx, dy):
        self.system = system
        self.lat_o = float(lat_o)
        self.lng_o = float(lng_o)
        self.dlat = float(dlat)
        self.dlng = float(dlng)
        self.dx = float(dx)
        self.dy = float(dy)

    def getGPS(self, x, y, z):

        lat = self.lat_o + (y*self.dlat)/self.dy
        lng = self.lng_o + (x*cos(radians(lat))*self.dlng)/self.dx

        return lat, lng, z

    def getIndoor(self, lat, lng, alt):

        vs = self.dy/self.dlat
        hs = self.dx/(cos(radians(lat))*self.dlng)

        x = (lng - self.lng_o) * hs
        y = (lat - self.lat_o) * vs

        return x, y, alt

@app.route('/sources')
def sources():
    sourceList = getSources()
    response = {}
    response['sensors'] = sourceList
    json_response = json.dumps(response)
    return(json_response)

@app.route('/sensors')
def sensors():
    if DEBUG:
        print('Requested')

    source = request.args.get('source')

    sensorList = getSensors(source)

    response = {}
    response['sensors'] = sensorList
    json_response = json.dumps(response)
    return(json_response)

@app.route('/features')
def features():

    sensor = request.args.get('sensor')

    featureList = getFeatures(sensor)

    response = {}
    response['features'] = featureList
    json_response = json.dumps(response)
    return(json_response)


systemsDict = initialize_indoor_systems()

app.run(port=5000,debug=DEBUG)
