"use strict"

from os import listdir, path
import json
from collections import defaultdict
import sys
from datetime import datetime
import time
from flask import request
from pathlib import Path

from classes.utils import Utils

import requests

DEBUG = True

###################################################################
#
# READINGS DataAPI
#
###################################################################

#r = requests.get('https://api.github.com/repos/psf/requests')
#r.json()["description"]

class DataAPI(object):

    def __init__(self, settings):
        print("Initializing SENSORS DataAPI")
        self.settings = settings
        self.basePath = self.settings['readings_base_path']

#################################################################
#  API FUNCTIONS                                                #
#################################################################

    #NEW API FUNCTION
    #returns sensor reading for X sensors
    def get(self, acp_id):
        try:
            print("get " + acp_id)
            reading = self.get_latest_reading(acp_id)
        except:
            print('get() sensor {} not found'.format(acp_id))
            print(sys.exc_info())
            return "{}"
        response = { "acp_reading": reading }
        json_response = json.dumps(response)
        return json_response

    def get_day(self, acp_id, args):
        #DEBUG source, feature, date will come from args or sensor data
        source = 'mqtt_acp'

        selected_date = Utils.getDateToday()

        fname = ( Path(self.basePath)
                    .resolve()
                    .joinpath(source,
                              'sensors',
                              acp_id,
                              date_to_sensorpath(selecteddate),acp_id+'_'+selected_date+'.txt')
                ) # brackets to allow line breaks

        readings = []

        with open(fname, 'r') as readings_file:
            readings_data = readings_file.read()

        for reading in readings_data: # iterate lines in .txt file
            readings += json.loads(reading)

        # parse file
        readings = json.loads(readings_data)

        latestData = open(fname).readlines()[-1]
        jsonData = json.loads(latestData)

        response = {}

        if feature == '' or feature == None:
            response = {'features':jsonData['payload_fields']}
        else:
            response = {feature:jsonData['payload_fields'][feature]}

        json_response = json.dumps(response)
        return json_response

    def history_data(self, args):
        if DEBUG:
            print('history_data() Requested')

        try:
            selecteddate = args.get('date')
            source = args.get('source')
            sensor = args.get('sensor')
            feature = args.get('feature')
        except:
            print("history_data() args error")
            if DEBUG:
                print(sys.exc_info())
                print(args)
            return '{ "data": [] }'

        workingDir = ''
        rdict = defaultdict(float)
        print(request)
        workingDir = ( Path(self.basePath)
                        .resolve()
                        .joinpath(source,'data_bin',self.date_to_path(selecteddate))
                     )
        if not path.exists(workingDir):
            print("history_data() bad data path "+workingDir)
            if DEBUG:
                print(args)
            return '{ "data": [] }'

        response = {}
        response['data'] = []

        for f in listdir(workingDir):
            fpath = Path(workingDir).resolve().joinpath(f)
            with open(fpath) as json_file:
                data = json.load(json_file)
                if data['acp_id'] == sensor:
                    try:
                        rdict[float(f.split('_')[0])] = data['payload_fields'][feature]
                    except KeyError:
                        pass

        for k in sorted(rdict.keys()):
            response['data'].append({'ts':str(k), 'val':rdict[k]})

        response['date'] = selecteddate
        response['sensor'] = sensor
        response['feature'] = feature

        json_response = json.dumps(response)
        return(json_response)

#################################################################
#  SUPPORT FUNCTIONS                                            #
#################################################################

    def date_to_path(self, selecteddate):
        data = selecteddate.split('-')
        return(data[0]+'/'+data[1]+'/'+data[2]+'/')

    def date_to_sensorpath(self, selecteddate):
        data = selecteddate.split('-')
        return(data[0]+'/'+data[1]+'/')

    #HELPER FUNCTION FOR NEW API
    #returns most recent readings
    def get_recent_readings(self,sensor):
        sensor_path = self.basePath + 'mqtt_acp/sensors/'
        selecteddate = Utils.getDateToday()
       #load the sensor lookup table
        response={}
        file_dir=sensor_path+sensor+'/'+Utils.date_to_sensorpath(selecteddate)+sensor+"_"+Utils.date_to_sensorpath_name(selecteddate)+".txt"

        print("attempting:",file_dir)

        #adding try/catch here in case we add sensor which has not yet sent any data
        try:
            ip=open("./"+file_dir)
            lines = ip.read().splitlines()
            last_line = lines[-1]
            jstr = last_line.strip()
            jdata = json.loads(jstr)

            response[sensor]=jdata["payload_fields"]

        except:
            print("no such sensor found, next")

        return response

    def get_latest_reading(self, acp_id):
        #DEBUG source, feature, date will come from args or sensor data
        source = 'mqtt_acp'

        today = Utils.getDateToday()

        fname = ( Path(self.basePath)
                    .resolve()
                    .joinpath(source,
                              'sensors',
                              acp_id,
                              self.date_to_sensorpath(today),acp_id+'_'+today+'.txt')
                ) # brackets to allow line breaks

        print("get_latest_reading() file {}".format(fname))

        reading_str = open(fname).readlines()[-1]

        reading = json.loads(reading_str)

        return reading
