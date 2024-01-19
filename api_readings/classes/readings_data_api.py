"use strict"

from os import listdir, path
import json
from collections import defaultdict
import sys
from datetime import datetime
import time
import datetime
from flask import request, make_response
from pathlib import Path
from jsonpath_ng import jsonpath, parse
from statistics import mean
from statistics import stdev

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

class ReadingsDataAPI(object):

    def __init__(self, settings):
        print("Initializing SENSORS DataAPI")
        self.settings = settings
        self.basePath = self.settings['readings_base_path']

#################################################################
#  API FUNCTIONS                                                #
#################################################################

    # /get/<acp_id> returns most recent sensor reading for sensor
    # Note this returns data from the most recent message from the sensor,
    # which, depending on the sensor, may contain values for a subset of
    # the features.
    def get(self, acp_id, args):
        print('invoking get')
        response_obj = {}
        try:
            if DEBUG:
                args_str = ""
                for key in args:
                    args_str += key+"="+args.get(key)+" "
                print("get {}/{}".format(acp_id,args_str) )
            # Lookup the sensor metadata, this will include the
            # filepath to the readings, and also may be returned
            # in the response.
            sensor_info = self.get_sensor_info(acp_id)

            type_info = sensor_info["acp_type_info"]

            today = Utils.getDateToday()
            print(today)
            records = self.get_day_records(acp_id, today, type_info)

            print(records)
            if len(records) > 0:
                response_obj["reading"] = json.loads(records[-1])

            if "metadata" in args and args["metadata"] == "true":
                response_obj["sensor_metadata"] = sensor_info
        except:
            print('get() sensor {} not found'.format(acp_id))
            print(sys.exc_info())
            return '{ "acp_error_msg": "readings_data_api get Exception" }'
        json_response = json.dumps(response_obj)
        response = make_response(json_response)
        response.headers['Content-Type'] = 'application/json'
        return response

    # /get_day/<acp_id>/[?date=YY-MM-DD][&metadata=true]
    def get_day(self, acp_id, args):
        print('invoking get day')
        response_obj = {}

        # Lookup the sensor metadata, this will include the
        # filepath to the readings, and also may be returned
        # in the response.
        sensor_info = self.get_sensor_info(acp_id)

        if "metadata" in args and args["metadata"] == "true":
            response_obj["sensor_metadata"] = sensor_info

        # Only get readings if sensor_info is not {}
        if bool(sensor_info):
            try:
                if DEBUG:
                    args_str = ""
                    for key in args:
                        args_str += key+"="+args.get(key)+" "
                    print("get_day() {}/{}".format(acp_id,args_str) )

                if "date" in args:
                    selected_date = args.get("date")
                else:
                    selected_date = Utils.getDateToday()

                records = self.get_day_records(acp_id, selected_date, sensor_info["acp_type_info"])
                readings = []

                for line in records:
                    readings.append(json.loads(line))

                response_obj["readings"] = readings

            except FileNotFoundError as e:
                print(f'get() sensor {acp_id} readings for {selected_date} not found',file=sys.stderr)
                print(sys.exc_info())
                response_obj = {}
                response_obj["acp_error_id"] = "NO_READINGS"
                response_obj["acp_error_msg"] = "readings_data_api get_day() Exception "+str(e.__class__)
        else:
            response_obj = {}
            response_obj["acp_error_id"] = "NO_METADATA_FOR_SENSOR"
            response_obj["acp_error_msg"] = "No metadata available for this sensor, so location of readings is unknown"

        json_response = json.dumps(response_obj)
        response = make_response(json_response)
        response.headers['Content-Type'] = 'application/json'
        return response

    # /get_feature/<acp_id> returns most recent sensor reading for sensor + feature
    def get_feature(self, acp_id, feature_id, args):
        response_obj = {}
        try:
            if DEBUG:
                args_str = ""
                for key in args:
                    args_str += key+"="+args.get(key)+" "
                print(f"Readings API get_feature {acp_id}/{feature_id}/{args_str}", file=sys.stderr)

            # Lookup the sensor metadata, this will include the
            # filepath to the readings, and also may be returned
            # in the response.
            sensor_info = self.get_sensor_info(acp_id)

            feature_reading = self.get_feature_reading(acp_id, feature_id, sensor_info["acp_type_info"], args)

            if feature_reading is not None:
                response_obj["reading"] = feature_reading

            if "metadata" in args and args["metadata"] == "true":
                response_obj["sensor_info"] = sensor_info
        except:
            print(f'get_feature() sensor {acp_id} exception', file=sys.stderr)
            print(sys.exc_info(), file=sys.stderr)
            return '{ "acp_error_msg": "readings_data_api get_feature Exception" }'
        json_response = json.dumps(response_obj)
        response = make_response(json_response)
        response.headers['Content-Type'] = 'application/json'
        return response

    # /get_floor_feature/<system>/<floor>/<feature>/ returns most recent sensor reading for
    # all sensors with required feature on a given floor
    # E.g. /api/sensors/get_floor_feature/WGB/1/temperature
    # { readings: { dict acp_id -> reading }
    #   sensors: { dict acp_id -> sensor metadata }
    #   sensor_types: { dict acp_type_id -> sensor type metadata }
    # }
    def get_floor_feature(self, system, floor, feature_id, args):
        print('\n\n\nINITIATING CODE FORE get_floor_feature', args,'\n\n\n')
        #t1 = datetime.now()
        response_obj = {}
        try:
            if DEBUG:
                args_str = ""
                for key in args:
                    args_str += key+"="+args.get(key)+" "
                print(f"Readings API get_floor_feature {system}/{floor}/{feature_id}/{args_str}", file=sys.stderr)

            # Call Sensors API to find sensors on given floor
            # get_floor_sensors returns:
            # { "sensors": { },
            #   "sensor_type_info": {} #DEBUG will change to "sensor_types"
            # }
            floor_sensors = self.get_floor_sensors(system, floor)

            # Filter the sensor types to only those containing feature (maybe do this in sensors API)
            sensor_types = {}
            for acp_type_id in floor_sensors["sensor_type_info"]: #DEBUG ["sensor_types"]
                if feature_id in floor_sensors["sensor_type_info"][acp_type_id]["features"]:
                    sensor_types[acp_type_id] = floor_sensors["sensor_type_info"][acp_type_id]
            # print(f'feature sensor_types: {sensor_types}')

            # Filter the sensors to only include sensor_types with feature
            sensors = {}
            for acp_id in floor_sensors["sensors"]:
                if "acp_type_id" in floor_sensors["sensors"][acp_id] and floor_sensors["sensors"][acp_id]["acp_type_id"] in sensor_types:
                    sensors[acp_id] = floor_sensors["sensors"][acp_id]

            if "metadata" in args and args["metadata"] == "true":
                response_obj["sensors"] = sensors
                response_obj["sensor_types"] = sensor_types

            readings = {}

            for acp_id in sensors:
                sensor_info = sensors[acp_id]
                type_info = sensor_types[sensor_info["acp_type_id"]]
                ##pass the date here
                feature_reading = self.get_feature_reading(acp_id, feature_id, type_info, args)
                if feature_reading is not None:
                    readings[acp_id] = feature_reading

            response_obj["readings"] = readings

        except:
            print(f'get_floor_feature() sensor {system} {floor} {feature_id} exception', file=sys.stderr)
            print(sys.exc_info(), file=sys.stderr)
            return '{ "acp_error_msg": "readings_data_api get_floor_feature Exception" }'
        json_response = json.dumps(response_obj)
        response = make_response(json_response)
        response.headers['Content-Type'] = 'application/json'
        # print(f'time: {datetime.now()-t1}')

        return response


      # /get_day/<acp_id>/[?date=YY-MM-DD][&metadata=true]
    def get_day_cerberus(self, acp_id, args):
        print('invoking get day CERBERUS')
        response_obj = {}

        # Lookup the sensor metadata, this will include the
        # filepath to the readings, and also may be returned
        # in the response.

        with open('./mock_clarence/cerberus_middle_metadata.json') as f:
           sensor_info = json.load(f)

           
        #sensor_info = self.get_sensor_info(acp_id)
        print(sensor_info)
        print("\n", "done printing","\n")
        if "metadata" in args and args["metadata"] == "true":
            response_obj["sensor_metadata"] = sensor_info

        print("entering bool")
        # Only get readings if sensor_info is not {}
        if bool(sensor_info):
            print("bool")
            try:
                if DEBUG:
                    args_str = ""
                    for key in args:
                        args_str += key+"="+args.get(key)+" "
                    print("get_day_clarence() {}/{}".format(acp_id,args_str) )

                if "date" in args:
                    selected_date = args.get("date")
                else:
                    selected_date = Utils.getDateToday()

                print("getting day records -- clarence","\n")
                records = self.get_day_records(acp_id, selected_date, sensor_info["acp_type_info"])

                print("getting day records -- clarence")
                print(sensor_info["acp_type_info"])
                readings = []

                for line in records:
                    readings.append(json.loads(line))
                print("TOTAL READINGS LEN", len(readings), "\n")
                response_obj["readings"] = readings

            except FileNotFoundError as e:
                print(f'get() sensor {acp_id} readings for {selected_date} not found',file=sys.stderr)
                print(sys.exc_info())
                response_obj = {}
                response_obj["acp_error_id"] = "NO_READINGS"
                response_obj["acp_error_msg"] = "readings_data_api get_day() Exception "+str(e.__class__)
        else:
            response_obj = {}
            response_obj["acp_error_id"] = "NO_METADATA_FOR_SENSOR"
            response_obj["acp_error_msg"] = "No metadata available for this sensor, so location of readings is unknown"

        json_response = json.dumps(response_obj)
        response = make_response(json_response)
        response.headers['Content-Type'] = 'application/json'
        return response


      # /get_day/<acp_id>/[?date=YY-MM-DD][&metadata=true]
    def get_day_clarence(self, acp_id, args):
        print('invoking get day clarence')
        response_obj = {}

        # Lookup the sensor metadata, this will include the
        # filepath to the readings, and also may be returned
        # in the response.

        with open('./mock_clarence/sensor_metadata.json') as f:
           sensor_info = json.load(f)

           
        #sensor_info = self.get_sensor_info(acp_id)
        print(sensor_info)
        print("\n", "done printing","\n")
        if "metadata" in args and args["metadata"] == "true":
            response_obj["sensor_metadata"] = sensor_info

        print("entering bool")
        # Only get readings if sensor_info is not {}
        if bool(sensor_info):
            print("bool")
            try:
                if DEBUG:
                    args_str = ""
                    for key in args:
                        args_str += key+"="+args.get(key)+" "
                    print("get_day_clarence() {}/{}".format(acp_id,args_str) )

                if "date" in args:
                    selected_date = args.get("date")
                else:
                    selected_date = Utils.getDateToday()

                print("getting day records -- clarence","\n")
                records = self.get_day_records(acp_id, selected_date, sensor_info["acp_type_info"])

                print("getting day records -- clarence")
                print(sensor_info["acp_type_info"])
                readings = []

                for line in records:
                    readings.append(json.loads(line))
                print("TOTAL READINGS LEN", len(readings), "\n")
                response_obj["readings"] = readings

            except FileNotFoundError as e:
                print(f'get() sensor {acp_id} readings for {selected_date} not found',file=sys.stderr)
                print(sys.exc_info())
                response_obj = {}
                response_obj["acp_error_id"] = "NO_READINGS"
                response_obj["acp_error_msg"] = "readings_data_api get_day() Exception "+str(e.__class__)
        else:
            response_obj = {}
            response_obj["acp_error_id"] = "NO_METADATA_FOR_SENSOR"
            response_obj["acp_error_msg"] = "No metadata available for this sensor, so location of readings is unknown"

        json_response = json.dumps(response_obj)
        response = make_response(json_response)
        response.headers['Content-Type'] = 'application/json'
        return response


#################################################################
#  SUPPORT FUNCTIONS                                            #
#################################################################

    #returns day's worth of readings for an entire crate, ie FF-GW20
    #makes suse of the get_day_records after being supplied a list
    #of sensors in that crate, takese crate, day and type as arguments

    #get bim
     # Get sensors for a given crate_id, returning dictionary of sensors
    # def get_bim(self, coordinate_system, crate_id):
    #     #iterate through sensors.json and collect all crates
    #     sensor_list_obj = {}

    #     for acp_id in SENSORS:
    #         sensor = SENSORS[acp_id]
    #         if ( "crate_id" in sensor and
    #              sensor["crate_id"] == crate_id ):
    #             sensor_list_obj[acp_id] =  sensor

    #     self.add_xyzf(coordinate_system, sensor_list_obj)

    #     return { 'sensors': sensor_list_obj }

     # /get_floor_feature/<system>/<floor>/<feature>/ returns most recent sensor reading for
    # all sensors with required feature on a given floor
    # E.g. /api/sensors/get_floor_feature/WGB/1/temperature
    # { readings: { dict acp_id -> reading }
    #   sensors: { dict acp_id -> sensor metadata }
    #   sensor_types: { dict acp_type_id -> sensor type metadata }
    # }
    def get_crate_feature(self, system, floor, feature_id, args):
        #t1 = datetime.now()
        response_obj = {}
        try:
            if DEBUG:
                args_str = ""
                for key in args:
                    args_str += key+"="+args.get(key)+" "
                print(f"Readings API get_crate_feature {system}/{floor}/{feature_id}/{args_str}", file=sys.stderr)

            # Call Sensors API to find sensors on given floor
            # get_floor_sensors returns:
            # { "sensors": { },
            #   "sensor_type_info": {} #DEBUG will change to "sensor_types"
            # }
            floor_sensors = self.get_floor_sensors(system, floor)

            # Filter the sensor types to only those containing feature (maybe do this in sensors API)
            sensor_types = {}
            for acp_type_id in floor_sensors["sensor_type_info"]: #DEBUG ["sensor_types"]
                if feature_id in floor_sensors["sensor_type_info"][acp_type_id]["features"]:
                    sensor_types[acp_type_id] = floor_sensors["sensor_type_info"][acp_type_id]
            # print(f'feature sensor_types: {sensor_types}')

            # Filter the sensors to only include sensor_types with feature
            sensors = {}
            for acp_id in floor_sensors["sensors"]:
                if "acp_type_id" in floor_sensors["sensors"][acp_id] and floor_sensors["sensors"][acp_id]["acp_type_id"] in sensor_types:
                    sensors[acp_id] = floor_sensors["sensors"][acp_id]

            if "metadata" in args and args["metadata"] == "true":
                response_obj["sensors"] = sensors
                response_obj["sensor_types"] = sensor_types

            readings = {}

            for acp_id in sensors:
                sensor_info = sensors[acp_id]
                type_info = sensor_types[sensor_info["acp_type_id"]]
                feature_reading = self.get_feature_reading(acp_id, feature_id, type_info, args)
                if feature_reading is not None:
                    readings[acp_id] = feature_reading

            response_obj["readings"] = readings

        except:
            print(f'get_crate_feature() sensor {system} {floor} {feature_id} exception', file=sys.stderr)
            print(sys.exc_info(), file=sys.stderr)
            return '{ "acp_error_msg": "readings_data_api get_crate_feature Exception" }'
        json_response = json.dumps(response_obj)
        response = make_response(json_response)
        response.headers['Content-Type'] = 'application/json'
        # print(f'time: {datetime.now()-t1}')

        return response

    # Get a day's-worth of sensor readings for required sensor as list of STRINGS (one per reading)
    # readings_day will be "YYYY-MM-DD"
    # sensor_info is required to work out where the data is stored
    def get_day_records(self, acp_id, readings_day, sensor_type_info):
        print('invoking get day records')

        try:
            YYYY = readings_day[0:4]
            MM   = readings_day[5:7]
            DD   = readings_day[8:10]

            day_file = sensor_type_info["day_file"]

            readings_file_name = ( day_file.replace("<acp_id>",acp_id)
                                           .replace("<YYYY>",YYYY)
                                           .replace("<MM>",MM)
                                           .replace("<DD>",DD)
            )

            print("get_day_records() readings_file_name {}".format(readings_file_name))
        except:
            print("get_day_records() no data for {} on {}".format(acp_id,readings_day))
            return []
        try:
            readings = open(readings_file_name, "r").readlines()
        except FileNotFoundError:
            readings = []

        return readings

    # get_feature_reading(acp_id, feature_id, type_info)
    # Uses type_info to find jsonpath to feature in reading, and
    # loads readings day file for sensor and iterates back through it
    # for the latest reading for that feature.
    # Returns 'reading' JSON object (i.e. message as sent by sensor)
    def get_feature_reading(self, acp_id, feature_id, type_info, args):

        #print(f'Readings API get_feature_reading {acp_id} {feature_id} \ntype_info:{type_info}',file=sys.stderr)

        path = parse(f'$.features[{feature_id}].jsonpath')

        try:
            value_path_str = path.find(type_info)[0].value
            #print(f'get_feature value_path "{value_path_str}"')
            value_path = parse(value_path_str)
        except:
            return f'{{ "acp_error_msg": "readings_data_api get_feature no {acp_id}/{feature_id}" }}'



        #instead of today get date as an argument

        if "date" in args:
            selected_date = args.get("date")
        else:
            selected_date = Utils.getDateToday()

        records = self.get_day_records(acp_id, selected_date, type_info)

        #print(f'records length={len(records)}') #DEBUG

        # Loop backwards through the day's records until we find one with the required feature
        # NOTE each reading is a STRING
        for reading in reversed(records):
            try:
                reading_obj = json.loads(reading)
                if len(value_path.find(reading_obj)) > 0:
                    return reading_obj
            except IndexError:
                continue

        #print(f'get_feature_reading() {acp_id} returning None',file=sys.stderr)
        return None


    #################################################
    # Get data from the Sensors API
    #################################################

    def get_sensor_info(self, acp_id):
        print("get_sensor_info() {}".format(acp_id))
        sensors_api_url = self.settings["API_SENSORS"]+'get/'+acp_id+"/"
        print('sensors api url',sensors_api_url)
        
        #fetch data from Sensors api
        try:
            print('sensor', acp_id, sensors_api_url)
            print('trying to get response for', acp_id)
            response = requests.get(sensors_api_url)
            response.raise_for_status()
            # access JSON content
            sensor_info = response.json()
       # except HTTPError as http_err:
       #     print('some HTTP error')
       #     print(f'get_sensor_info() HTTP GET error occurred: {http_err}')
       #     return { "acp_error_msg": "readings_data_api: get_sensor_info() HTTP error." }
        except Exception as err:
            print(f'get_sensor_info() Other GET error occurred: {err}')
            return { "acp_error_msg": "readings_data_api: Exception in get_sensor_info()."}
        return sensor_info


    #################################################
    #                Helper Functions               #
    #################################################
    def get_crate_chart(self, system, crate,args):

        print('getting crate charts', crate)
        if "date" in args:
            selected_date = args.get("date")
        else:
            selected_date = Utils.getDateToday()

        date=[2022,2,27]
        diena=selected_date
        
        month=str(date[1])
        if len(month)==1:
            month='0'+month
        day=str(date[2])
        if len(day)==1:
            day='0'+day

        print('selected', selected_date, 'hardcoded',str(date[0])+'-'+month+'-'+day)
        print('OG args', args)
        #args={'date':diena}#hardcoded

        ##GET ALL SENSORS FROM A CRATE SPECIFIED IN ARGS
        crate_sensors=self.get_crate_sensors(system, crate, args)
        print('ALL SENSORS IN ', crate, 'ARE', crate_sensors)

        #if date argument exists then parse it
        #date='today'
      #  return crate_sensors
        sensor_data={'readings':[]}
        try:
            # sensor_list=[]
# 
            # sensor_data={}
            
            #GET A DAY'S TIMESTAMPS FROM MIDNIGHT START TO MIDNIGHT END
            day_ts=self.get_days_range(selected_date)#hardcoded

            ts_division=5*60
            ts_threshold=60*6
            
            ts_list=self.split_time(day_ts[0],day_ts[1],ts_division)#60s x 5min
            iterator=0

            #ITERATE THROUGH TIMSTAMPS TO COMPUTE READINGS FOR EVERY SINGLE ONE
            for timestamp in ts_list:
                sensor_iterator=0
                sensors_used=[]
               # print(timestamp)
                sensor_data['readings'].append({'acp_ts':timestamp})
                
                payload_tracker={'co2':[], 'temperature':[], 'humidity':[]}
                ts_tracker={}
                ts_list=[]
                last_sensor=''#IDK WHAT THIS DOES

                #FOR A GIVEN TIMETAMP ROLL ACROSS ALL SENSORS AND GET READINGS AVERAGES
                for sensor in crate_sensors:
    
                    payload_list=crate_sensors[sensor]['readings']
                    
                    get_index=self.binary_search_recursive(payload_list,timestamp,0,len(payload_list)-1)
                    
                    #print(len(payload_list)-1, get_index)

                    if (get_index==-1):
                        continue
                        
                    payload=payload_list[get_index]['payload_cooked']
                    acp_ts=payload_list[get_index]['acp_ts']
                    ts_tracker[sensor]=acp_ts
                    ts_list.append(int(float(acp_ts)))
                    print(sensor)

                   
                    if "co2" in payload:
                        if ((payload['co2']>0) and (abs(int(float(acp_ts))-timestamp)<ts_threshold)):
                            payload_tracker['co2'].append(payload['co2'])
                            last_sensor=sensor ##make sure that metadata comes from a co2 sensor
                    
                    if "temperature" in payload:
                        if ((payload['temperature']>0) and (abs(int(float(acp_ts))-timestamp)<ts_threshold)):
                            payload_tracker['temperature'].append(payload['temperature'])

                    if "humidity" in payload:
                        if ((payload['humidity']>0) and (abs(int(float(acp_ts))-timestamp)<ts_threshold)):
                            payload_tracker['humidity'].append(payload['humidity'])

                   # data_obj={}
                   # data_obj['std']=std
                   # data_obj['payload_cooked']=payload
                   # data_obj['acp_ts']=acp_ts
                   # data_obj['date']=datetime.datetime.fromtimestamp(int(float(acp_ts)))

                    #sensor_data['readings'][timestamp][sensor]=data_obj
                    #sensor_data['readings'].append(data_obj)
                    

                sensor_info = self.get_sensor_info(sensor)#last_sensor
                sensor_data["sensor_metadata"] = sensor_info
                sensor_data['readings'][iterator]['acp_id']='elsys-co2-CRATE'
                sensor_data['readings'][iterator]['acp_type_id']='elsys-co2'
                sensor_data['readings'][iterator]['date']=datetime.datetime.fromtimestamp(timestamp)
                sensor_data['readings'][iterator]['ts_list']=ts_list
                sensor_data['readings'][iterator]['ts_mean']=mean(ts_list)
                sensor_data['readings'][iterator]['ts_std']=stdev(ts_list)

                print('co2',payload_tracker['co2'])
                if(len(payload_tracker['co2'])==0):
                    co2=None
                else:
                    co2=round(mean(payload_tracker['co2']),2)
                
                #temperature=round(mean(payload_tracker['temperature']),2)

                if(len(payload_tracker['temperature'])==0):
                    temperature=None
                else:
                    temperature=round(mean(payload_tracker['temperature']),2)

                if(len(payload_tracker['humidity'])==0):
                    humidity=None
                else:
                    humidity=round(mean(payload_tracker['humidity']),2)
                    
                #humidity=round(mean(payload_tracker['humidity']),2)
                
                sensor_data['readings'][iterator]['payload_cooked']={'co2':co2, 'temperature':temperature, 'humidity':humidity}     
                iterator+=1
                print(iterator)

              
         

                   # data_obj['std']=std
                   # sensor_data['readings'].append(data_obj)        
                   # print('\nSENSOR:', sensor)
                   #sensor_list.append(sensor_list)
        except HTTPError as http_err:
            print(f'get_crate_chart() HTTP GET error occurred: {http_err}')
            return { "acp_error_msg": "readings_data_api: get_crate_chart() HTTP error." }
        except Exception as err:
            print(f'get_crate_chart() Other GET error occurred: {err}', err)
            return { "acp_error_msg": "readings_data_api: Exception in get_crate_chart()."}
        return sensor_data#'done'#floor_sensors
        
               
    def binary_search_recursive(self, array, element, start, end):
        if start > end:
            return -1
        
        mid = (start + end) // 2

        arr_val=int(float(array[mid]['acp_ts']))

        if abs(element - arr_val)<450:
            return mid
    
        if element < arr_val:
            return self.binary_search_recursive( array, element, start, mid-1)
        else:
            return self.binary_search_recursive( array, element, mid+1, end)

    ##get days worth of unix timestamps for 00:00 and 23:59
    def get_days_range(self,date): #YYYY,MM,DD
      print('getting day range', date)
      if date=='today':
        presentDate = datetime.datetime.now()
      else:
        datetime_object = datetime.datetime.strptime(date, '%Y-%m-%d')
        presentDate= datetime_object#datetime.datetime(date[0],date[1],date[2])
    
      presentDate = presentDate.replace(minute=0, hour=0, second=0)
      unix_timestamp = int(datetime.datetime.timestamp(presentDate))
      ts_start=unix_timestamp
    
      if date=='today':
        presentDate = datetime.datetime.now()
      else:
        presentDate = presentDate.replace(minute=59, hour=23, second=59)
        
      unix_timestamp = int(datetime.datetime.timestamp(presentDate))
      ts_end=unix_timestamp
      print('range',[ts_start, ts_end])
      return [ts_start, ts_end]

    #split time between two timestamps in x intervals (in seconds)
    def split_time(self,start,end, split):
      ts_list=[]
      start=int(start)
      end=int(end)
      iterator=start
      print(iterator,end)
      while(iterator<end):
        ##print(datetime.datetime.utcfromtimestamp(iterator).strftime('%Y-%m-%d %H:%M:%S'))
        ts_list.append(iterator)
        iterator+=split  
      return ts_list

      
    #################################################
    # Get sensors for a floor from the Sensors API
    #################################################

    # E.g. get_floor_sensors('WGB',1)
    def get_floor_sensors(self, system, floor):
        print(f"Readings API get_floor_sensors {system} {floor}")
        sensors_api_url = self.settings["API_SENSORS"]+f'get_floor_number/{system}/{floor}/?metadata=true'
        print(sensors_api_url)
        #fetch data from Sensors api
        try:
            response = requests.get(sensors_api_url)
            response.raise_for_status()
            # access JSON content
            floor_sensors = response.json()
        except HTTPError as http_err:
            print(f'get_floor_sensors() HTTP GET error occurred: {http_err}')
            return { "acp_error_msg": "readings_data_api: get_floor_sensors() HTTP error." }
        except Exception as err:
            print(f'get_floor_sensors() Other GET error occurred: {err}')
            return { "acp_error_msg": "readings_data_api: Exception in get_floor_sensors()."}
        return floor_sensors


    # E.g. get_crate_sensors('WGB','FN07')
    def get_crate_sensors(self, system, crate,args):
    
        print(f"Readings API get_crate_sensors {system} {crate}")
        print('\nALL args- ',args)
        #sensors_api_url = self.settings["API_SENSORS"]+f'get_bim/{system}/{crate}'
        #DEBUG only, I know it's not how it's supposed to be 
        sensors_api_url = self.settings["API_SENSORS"]+'get_bim/'+str(system)+'/'+str(crate)+'/'#http://adacity-jb.al.cl.cam.ac.uk/api/sensors/'+f'get_bim/{system}/{crate}'
        print('\nSENSOR URL: ',sensors_api_url,'\n')

        #fetch data from Sensors api
        try:
            response = requests.get(sensors_api_url)
            response.raise_for_status()
            # access JSON content
            crate_sensors = response.json()
            sensor_list=[]

            sensor_data={}

            for sensor in crate_sensors['sensors']:
                print('\nSENSOR:', sensor)
                sensor_list.append(sensor_list)
                #print('what',self.get_day2(sensor,args))
                #get day's worth of readings
                print('failing point in get_crate_sensors - getday2', sensor)
                sensor_data[sensor]=json.loads(self.get_day2(sensor,args))

                sensor_data[sensor]["acp_id"]=sensor

        
            print('\nTOTAL SENSORS IN ',crate,' : ',len(sensor_list))
        except HTTPError as http_err:
            print(f'get_crate_sensors() HTTP GET error occurred: {http_err}')
            return { "acp_error_msg": "readings_data_api: get_crate_sensors() HTTP error." }
        except Exception as err:
            print(f'get_crate_sensors() Other GET error occurred: {err}', err)
            return { "acp_error_msg": "readings_data_api: Exception in get_crate_sensors()."}
       
            
       
        return sensor_data
        #return crate_sensors

 # E.g. get_crate_sensors('WGB','FN07')
    def get_crate_roc(self, system, crate,args):
        print(f"Readings API get_crate_roc {system} {crate}")
        print('\nALL args- ',args)
        #sensors_api_url = self.settings["API_SENSORS"]+f'get_bim/{system}/{crate}'
        #DEBUG only, I know it's not how it's supposed to be 
        sensors_api_url = self.settings["API_SENSORS"]+'get_bim/'+str(system)+'/'+str(crate)+'/'#http://adacity-jb.al.cl.cam.ac.uk/api/sensors/'+f'get_bim/{system}/{crate}'
        print('\nSENSOR URL: ',sensors_api_url,'\n')

        #fetch data from Sensors api
        try:
            response = requests.get(sensors_api_url)
            response.raise_for_status()
            # access JSON content
            crate_sensors = response.json()
            sensor_list=[]

            sensor_data={}

            for sensor in crate_sensors['sensors']:
               # print('\nSENSOR:', sensor)
                sensor_list.append(sensor_list)
                #print('what',self.get_day2(sensor,args))
                #get day's worth of readings
                sensor_data[sensor]=json.loads(self.get_day3(sensor,args))

                sensor_data[sensor]["acp_id"]=sensor

        
            print('\nTOTAL SENSORS IN ',crate,' : ',len(sensor_list))
        except HTTPError as http_err:
            print(f'get_crate_roc() HTTP GET error occurred: {http_err}')
            return { "acp_error_msg": "readings_data_api: get_crate_sensors() HTTP error." }
        except Exception as err:
            print(f'get_crate_roc() Other GET error occurred: {err}')
            return { "acp_error_msg": "readings_data_api: Exception in get_crate_sensors()."}
       
            
       
        return sensor_data
        # /get_day/<acp_id>/[?date=YY-MM-DD][&metadata=true]

    ##use only for ROC visualisation
    def get_day3(self, acp_id, args):
        response_obj = {}

        # Lookup the sensor metadata, this will include the
        # filepath to the readings, and also may be returned
        # in the response.
        sensor_info = self.get_sensor_info(acp_id)

        #ALWAYS GET METADATA
        #if "metadata" in args and args["metadata"] == "true":
        response_obj["sensor_metadata"] = sensor_info

        # Only get readings if sensor_info is not {}
        if bool(sensor_info):
            try:
                if DEBUG:
                    args_str = ""
                    for key in args:
                        args_str += key+"="+args.get(key)+" "
                    print("get_day() {}/{}".format(acp_id,args_str) )

                if "date" in args:
                    selected_date = args.get("date")
                else:
                    selected_date = Utils.getDateToday()

                records = self.get_day_records(acp_id, selected_date, sensor_info["acp_type_info"])

                readings = []

                record_len=len(records)
                index=0
                #print('records len', record_len)

                while (index<record_len-1):
                    index+=1
                   # print(index) 
                    raw_metadata_prev=json.loads(records[index-1])
                
                    raw_metadata=json.loads(records[index])

                    cooked_metadata_prev={}
                    
                    cooked_metadata={}
                    
                    cooked_metadata["acp_feed_ts"]=raw_metadata["acp_feed_ts"]
                    cooked_metadata["acp_ts"]=raw_metadata["acp_ts"]
                    

                    cooked_metadata["acp_ts_prev"]=raw_metadata_prev["acp_ts"]
                    cooked_metadata["acp_ts_curr"]=raw_metadata["acp_ts"]

                    delta=float(raw_metadata["acp_ts"])-float(raw_metadata_prev["acp_ts"])
                                                                         
                    cooked_metadata["acp_ts_delta"]=round(delta,1) 
                    cooked_metadata["acp_id"]=raw_metadata["acp_id"]
                    cooked_metadata["acp_type_id"]=raw_metadata["acp_type_id"]

                   ## cooked_metadata["payload_cooked_prev"]=raw_metadata_prev["payload_cooked"]             
                   ## cooked_metadata["payload_cooked_curr"]=raw_metadata["payload_cooked"]

                    PC_prev=raw_metadata_prev["payload_cooked"]
                    PC_curr=raw_metadata["payload_cooked"]
                  
                    ts_prev=float(raw_metadata_prev["acp_ts"])
                    ts_curr=float(raw_metadata["acp_ts"])

                    bool_co2=False
                    bool_temp=False
                    bool_hum=False
                    if ("co2" in PC_prev) and ("co2" in PC_curr):
                        bool_co2=True

                    if ("humidity" in PC_prev) and ("humidity" in PC_curr):
                        bool_hum=True

                    if ("temperature" in PC_prev) and ("temperature" in PC_curr):
                        bool_temp=True

                    if(bool_co2 and bool_hum and bool_temp):
                        # #cooked_metadata=raw_metadata
                        
                        # roc_co2=((PC_curr['co2']/PC_prev['co2'])-1)*100
                        # roc_temp=((PC_curr['temperature']/PC_prev['temperature'])-1)*100
                        # roc_hum=((PC_curr['humidity']/PC_prev['humidity'])-1)*100

                        roc_co2=((PC_curr['co2']-PC_prev['co2'])/(ts_curr-ts_prev))*100
                        roc_temp=((PC_curr['temperature']-PC_prev['temperature'])/(ts_curr-ts_prev))*100
                        roc_hum=((PC_curr['humidity']-PC_prev['humidity'])/(ts_curr-ts_prev))*100



                        cooked_metadata["payload_cooked"]={'co2':round(roc_co2,2),'temperature':round(roc_temp,2),'humidity':round(roc_hum,2)}
                        #raw_metadata["payload_cooked"]
                        readings.append(cooked_metadata)
                    
                # for line in records:
                    # raw_metadata=json.loads(line)
                    # cooked_metadata={}
                    # cooked_metadata["acp_feed_ts"]=raw_metadata["acp_feed_ts"]
                    # cooked_metadata["acp_ts"]=raw_metadata["acp_ts"]
                    # cooked_metadata["acp_id"]=raw_metadata["acp_id"]
                    # cooked_metadata["acp_type_id"]=raw_metadata["acp_type_id"]
                    # cooked_metadata["payload_cooked"]=raw_metadata["payload_cooked"]
                    # if(len(cooked_metadata["payload_cooked"])>2):
                        # #cooked_metadata=raw_metadata
                        # readings.append(cooked_metadata)

                response_obj["readings"] = readings

                print('\nTOTAL READINGS FOR ',acp_id, ' : ',len(readings))

            except FileNotFoundError as e:
                print(f'get() sensor {acp_id} readings for {selected_date} not found',file=sys.stderr)
                print(sys.exc_info())
                response_obj = {}
                response_obj["acp_error_id"] = "NO_READINGS"
                response_obj["acp_error_msg"] = "readings_data_api get_day() Exception "+str(e.__class__)
        else:
            response_obj = {}
            response_obj["acp_error_id"] = "NO_METADATA_FOR_SENSOR"
            response_obj["acp_error_msg"] = "No metadata available for this sensor, so location of readings is unknown"

        #print('RESPONSE', response_obj)
        json_response = json.dumps(response_obj)
        response = make_response(json_response)
        response.headers['Content-Type'] = 'application/json'
        #print('\n\ntype: ',type(json_response))
        return json_response

    def get_day2(self, acp_id, args):
        response_obj = {}

        # Lookup the sensor metadata, this will include the
        # filepath to the readings, and also may be returned
        # in the response.
        print('FAILING POINT -get_day2 get_sensor_info', acp_id)
        sensor_info = self.get_sensor_info(acp_id)
        print('sensor info ack', acp_id)
        if "metadata" in args and args["metadata"] == "true":
            response_obj["sensor_metadata"] = sensor_info

        # Only get readings if sensor_info is not {}
        if bool(sensor_info):
            try:
                if DEBUG:
                    args_str = ""
                    for key in args:
                        args_str += key+"="+args.get(key)+" "
                    print("get_day() {}/{}".format(acp_id,args_str) )

                if "date" in args:
                    selected_date = args.get("date")
                else:
                    selected_date = Utils.getDateToday()

                records = self.get_day_records(acp_id, selected_date, sensor_info["acp_type_info"])

                readings = []

                for line in records:
                    raw_metadata=json.loads(line)
                    cooked_metadata={}
                    cooked_metadata["acp_feed_ts"]=raw_metadata["acp_feed_ts"]
                    cooked_metadata["acp_ts"]=raw_metadata["acp_ts"]
                    cooked_metadata["acp_id"]=raw_metadata["acp_id"]
                    cooked_metadata["acp_type_id"]=raw_metadata["acp_type_id"]
                    cooked_metadata["payload_cooked"]=raw_metadata["payload_cooked"]
                    if(len(cooked_metadata["payload_cooked"])>2):
                        #cooked_metadata=raw_metadata
                        readings.append(cooked_metadata)

                response_obj["readings"] = readings

                print('\nTOTAL READINGS FOR ',acp_id, ' : ',len(readings))

            except FileNotFoundError as e:
                print(f'get() sensor {acp_id} readings for {selected_date} not found',file=sys.stderr)
                print(sys.exc_info())
                response_obj = {}
                response_obj["acp_error_id"] = "NO_READINGS"
                response_obj["acp_error_msg"] = "readings_data_api get_day() Exception "+str(e.__class__)
        else:
            response_obj = {}
            response_obj["acp_error_id"] = "NO_METADATA_FOR_SENSOR"
            response_obj["acp_error_msg"] = "No metadata available for this sensor, so location of readings is unknown"

        #print('RESPONSE', response_obj)
        json_response = json.dumps(response_obj)
        response = make_response(json_response)
        response.headers['Content-Type'] = 'application/json'
        #print('\n\ntype: ',type(json_response))
        return json_response
