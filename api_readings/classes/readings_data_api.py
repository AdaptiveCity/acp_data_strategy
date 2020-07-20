"use strict"

from os import listdir, path
import json
from collections import defaultdict
import sys
from datetime import datetime
import time
from flask import request, make_response
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
    def get(self, acp_id, args):
        response_obj = {}
        try:
            args_str = ""
            for key in args:
                args_str += key+"="+args.get(key)+" "
            print("get {}/{}".format(acp_id,args_str) )
            reading = self.get_latest_reading(acp_id)
            response_obj["reading"] = reading
            if "metadata" in args and args["metadata"] == "true":
                sensor_metadata = self.get_sensor_metadata(acp_id)
                response_obj["sensor_metadata"] = sensor_metadata
        except:
            print('get() sensor {} not found'.format(acp_id))
            print(sys.exc_info())
            return '{ "error": "readings_data_api get Exception" }'
        json_response = json.dumps(response_obj)
        response = make_response(json_response)
        response.headers['Content-Type'] = 'application/json'
        return response

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

    #################################################
    # Get data from the Sensors API
    #################################################

    def get_sensor_metadata(self, acp_id):
        sensors_api_url = self.settings["API_SENSORS"]+'get/'+acp_id+"/"
        #fetch data from Sensors api
        try:
            response = requests.get(sensors_api_url)
            response.raise_for_status()
            # access JSON content
            sensor_metadata = response.json()
        except HTTPError as http_err:
            print(f'get_sensor_metadata HTTP GET error occurred: {http_err}')
            return { "error": "readings_data_api: get_sensor_metadata() HTTP error." }
        except Exception as err:
            print(f'space_api.py Other GET error occurred: {err}')
            return { "error": "readings_data_api: Exception in get_sensor_metadata()."}

        return sensor_metadata
