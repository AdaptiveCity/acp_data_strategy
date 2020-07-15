
from os import listdir, path
import json
from collections import defaultdict
import sys
from datetime import datetime
import time
from flask import request
from classes.utils import Utils

import requests

DEBUG = False

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

    #NEW API FUNCTION
    #returns sensor reading for X sensors
    def get_sensor_readings_for(self, acp_id):
        try:
            retrieved=self.get_recent_readings(acp_id)
        except:
            return 'no such sensor found'
        return retrieved

    #HELPER FUNCTION FOR NEW API
    #returns most recent readings
    def get_recent_readings(self,sensor):
        sensor_path = self.settings['readings_base_path']+'mqtt_acp/sensors/'
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

