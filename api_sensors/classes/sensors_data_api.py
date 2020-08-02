from os import listdir, path
import json
from collections import defaultdict
import sys
from datetime import datetime
import time
import numpy
from flask import request

import requests
from requests.exceptions import HTTPError


DEBUG = True

###################################################################
#
# SENSORS DataAPI
#
###################################################################

SENSORS=None

SENSOR_TYPES=None

class DataAPI(object):

    def __init__(self, settings):
        global SENSORS, SENSOR_TYPES
        print("Initializing SENSORS DataAPI")
        self.settings = settings
        SENSORS = self.load_sensors()
        SENSOR_TYPES = self.load_sensor_types()
        print("{} loaded".format(settings["sensors_file_name"]))
        self.load_coordinate_systems()

    # Get the metadata for a given sensor (e.g. 'rad-ath-003d0f'), including the type metadata
    def get(self, acp_id):
        print("get {}".format(acp_id))
        global SENSORS, SENSOR_TYPES
        try:
            sensor_details = SENSORS[acp_id]
            if "acp_type_id" in sensor_details:
                acp_type_id = sensor_details["acp_type_id"]
                if acp_type_id in SENSOR_TYPES:
                    sensor_details["acp_type_info"] = SENSOR_TYPES[acp_type_id]
        except:
            print("get() no sensor id {}".format(acp_id))
            return {}
        return sensor_details

    # Get the metadata for a given sensor TYPE (e.g. 'rad-ath')
    def get_type(self, acp_type_id):
        print("get_type {}".format(acp_type_id))
        type_info = self.type_lookup(acp_type_id)
        return type_info if type_info is not None else {}

    def get_floor_number(self, coordinate_system, floor_number):
        print("SENSORS data_api get_floor_number({},{})".format(coordinate_system, floor_number))
        sensor_list_obj = {}
        # coords.f(acp_location) will return floor number
        coords = self.coordinate_systems[coordinate_system]

        for acp_id in SENSORS:
            #determine if the same floor
            sensor = SENSORS[acp_id]
            print("SENSORS api get_floor_number sensor={}".format(sensor))
            if "acp_location" in sensor:
                loc = sensor["acp_location"]
                if loc["system"] == coordinate_system and coords.f(loc) == int(floor_number):
                    sensor_list_obj[acp_id] = sensor

        self.add_xyzf(coordinate_system, sensor_list_obj)

        return { 'sensors': sensor_list_obj }

    # Get sensors for a given crate_id, returning dictionary of sensors
    def get_bim(self, coordinate_system, crate_id):
        #iterate through sensors.json and collect all crates
        sensor_list_obj = {}

        for acp_id in SENSORS:
            sensor = SENSORS[acp_id]
            if ( "crate_id" in sensor and
                 sensor["crate_id"] == crate_id ):
                sensor_list_obj[acp_id] =  sensor

        self.add_xyzf(coordinate_system, sensor_list_obj)

        return { 'sensors': sensor_list_obj }

    #DEBUG this function needs parameters or renaming
    #DEBUG moved from space API
    # Note we are using a 'list_obj', i.e. { "id1": { "acp_id": "id1", ..}, "id2": { "acp_id": "id2", ...} }
    def get_gps(self):
        sensor_list_obj = {}

        for acp_id in SENSORS:
            sensor = SENSORS[acp_id]
            if ( "acp_location" in sensor and
                 sensor["acp_location"]["system"] == "GPS" ):
                sensor_list_obj[acp_id] = sensor

        return { 'sensors': sensor_list_obj }

    # Return a list of sensor's metadata
    # Returns { sensors: [..], types: [..]}
    def list(self, args):
        # debug listing of querystring args
        if DEBUG:
            args_str = ""
            for key in args:
                args_str += key+"="+args.get(key)+" "
            print("list() {}".format(args_str) )
        # Set bool to include sensor type metadata
        include_type_info = "type_metadata" in args and args["type_metadata"] == "true"
        sensor_list_obj = {}
        type_list_obj = {}
        for acp_id in SENSORS:
            sensor = SENSORS[acp_id]
            if True:                   # Here's where we'd filter the results
                sensor_list_obj[acp_id] = sensor
                if include_type_info:
                    acp_type_id = sensor["acp_type_id"]
                    type_info = self.type_lookup(acp_type_id)
                    if type_info is not None:
                        type_list_obj[acp_type_id] = type_info

        # Build return object { sensors: [..], types: [..]}
        return_obj = { 'sensors': sensor_list_obj }
        if include_type_info:
            return_obj["types"] = type_list_obj

        return return_obj

    # Return a list of sensor type  metadata
    # Returns { types: { "elsys-ems": {...}, ... }}
    def list_types(self, args):
        # debug listing of querystring args
        if DEBUG:
            args_str = ""
            for key in args:
                args_str += key+"="+args.get(key)+" "
            print("list_types() {}".format(args_str) )
        # Set bool to include sensor type metadata
        type_list_obj = {}
        for acp_type_id in SENSOR_TYPES:
            if True:                   # Here's where we'd filter the results
                type_info = self.type_lookup(acp_type_id)
                type_list_obj[acp_type_id] = type_info

        return_obj = { }
        return_obj["types"] = type_list_obj

        return return_obj

    ###########################################################################
    #
    # Support functions
    #
    ###########################################################################

    # This loads the sensor metadata into memory - we could use a database live instead.
    def load_sensors(self):
        file_name=self.settings["sensors_file_name"]

        #Checks if sensors.json exits so we don't have to create it
        if(path.isfile(file_name)):
            #load sensors.json and create dict
            with open(file_name,'r') as json_file:
                #WGB= json.loads(json_file.read())
                sensors=json.load(json_file)
                print(file_name," loaded successfully in load_sensors()")
        else:
            print("sensors.json failed to load in load_sensors()")
            #think of another way to load it then as we can't just use data_api
            #global data_api
            #sensors=json.loads(data_api.sensor_data())
            #print(sensors)
        return sensors

    def load_sensor_types(self):
        file_name = self.settings["sensor_types_file_name"]

        #Checks if sensors.json exits so we don't have to create it
        if(path.isfile(file_name)):
            #load sensors.json and create dict
            with open(file_name,'r') as json_file:
                sensor_types = json.load(json_file)
                print(file_name," loaded successfully in load_sensor_types()")
        else:
            print("sensors.json failed to load in load_sensor_types()")
        return sensor_types

    def type_lookup(self, acp_type_id):
        global SENSOR_TYPES
        try:
            type_info = SENSOR_TYPES[acp_type_id]
        except:
            return None
        return type_info

    # Update a list_obj of objects with "acp_location_xyz" and "acp_boundary_xyz" properties
    #DEBUG this routine is common to api_bim and api_sensors so should be in acp_coordinates
    def add_xyzf(self, coordinate_system, list_obj):
        if list_obj is None:
            return

        for acp_id in list_obj:
            if "acp_location" not in list_obj[acp_id]:
                # We need acp_location to for the coordinate system
                continue # no acp_location in this object so skip
            obj = list_obj[acp_id]
            acp_location = obj["acp_location"]
            sensor_coordinate_system = acp_location["system"]
            if sensor_coordinate_system != coordinate_system:
                continue
            # Note the xyz coordinates may already be cached in the bim data
            if "acp_location_xyz" not in obj:
                obj["acp_location_xyz"] = self.coordinate_systems[coordinate_system].xyzf(acp_location)
            if "acp_boundary" in obj and "acp_boundary_xyz" not in obj:
                obj["acp_boundary_xyz"] = self.acp_boundary_to_xy(coordinate_system, obj["acp_boundary"])

        return

    #DEBUG this should be in acp_coordinates
    ####################################################################
    ### In-Building coordinate system -> XYZ coords                 ###
    ####################################################################

    # Convert the building coords boundaries into equivalent latlngs
    # acp_boundary is a list [{ boundary_type, boundary: [...] }...]
    def acp_boundary_to_xy(self, coordinate_system, acp_boundary):
        xy_boundaries = [] # this is the list we will return when completed
        for boundary_obj in acp_boundary:
            # create new gps_boundary object, with type set as original
            xy_boundary = { "boundary_type": boundary_obj["boundary_type"] }
            # add the latlng points to this object
            xy_boundary["boundary"] = self.points_to_xy(coordinate_system, boundary_obj["boundary"])
            # append this new object to the list
            xy_boundaries.append(xy_boundary)

        return xy_boundaries

    def points_to_xy(self, coordinate_system, points):
        xy_points = []
        for point in points:
            xy_point = self.point_to_xy(coordinate_system, point)
            xy_points.append(xy_point)

        return xy_points

    def point_to_xy(self, coordinate_system, point):
        return self.coordinate_systems[coordinate_system].xy(point)

    #DEBUG WE'LL DEPRECATE THIS FOR NOW
    ##NEW API FUNCTION
    def get_sensors_count(self, crate_id, depth):
        floors=['GF','FF','SF']
        sensor_locations=[]
        sensor_list=[]
        #iterate through sensors.json and collect all crates
        for sensor in SENSORS:
            sensor_locations.append(SENSORS[sensor]['crate_id'])

        #using numpy makes everythign easier as we want to find frequencies
        sensor_locations = numpy.array(sensor_locations)
        #acquire crate counts to see how often they appear on the list
        (unique, counts) = numpy.unique(sensor_locations, return_counts=True)

        #iterate over unique and counts to compile a dict of sensors
        i=0
        while(i<len(unique)):
            sensor_count={}
            sensor_count['crate_id']=str(unique[i])
            sensor_count['sensors']=int(counts[i])
            sensor_list.append(sensor_count)
            i+=1

        #determine if query for floors
        if(crate_id in floors):
            floor_response=[]
            total_sensors=0
            for objects in sensor_list:
                if objects['crate_id'][0]==crate_id[0]:
                    floor_response.append(objects)
                    total_sensors+=objects['sensors']
            if(depth>0):
                return {'data': floor_response}
            else:
                return {'data': {'crate_id':crate_id, 'sensors':total_sensors}}
        #determine if querying the entire building
        elif (crate_id=='WGB'):
            if depth<=1:
                floor_response=[]
                total_sensors=0
                for floor in floors:
                    total_floor_sensors=0
                    for sensor in sensor_list:
                        if sensor['crate_id'][0]==floor[0]:
                            total_floor_sensors+=sensor['sensors']
                    total_sensors+=total_floor_sensors
                    floor_response.append({'crate_id':floor,'sensors':total_floor_sensors})
                if depth==1:
                    return {'data': floor_response}
                else:
                    return {'data':{'crate_id':crate_id, 'sensors':total_sensors}}
            else:
                #returns data for crates that are in sensors.json
                return {'data': sensor_list}
        #must be room then, check in the list
        else:
            for objects in sensor_list:
                if objects['crate_id']==crate_id:
                    return {'data': objects }


        return 'no such query found'

    #https://en.wikipedia.org/wiki/Even-odd_rule
    def is_point_in_path(self,x: int, y: int, poly) -> bool:
        #Determine if the point is in the path.

        #Args:
        #  x -- The x coordinates of point.
        #  y -- The y coordinates of point.
        #  poly -- a list of tuples [(x, y), (x, y), ...]

        #Returns:
        #  True if the point is in the path.

        num = len(poly)
        i = 0
        j = num - 1
        c = False
        for i in range(num):
            if ((poly[i][1] > y) != (poly[j][1] > y)) and \
                    (x < poly[i][0] + (poly[j][0] - poly[i][0]) * (y - poly[i][1]) /
                                    (poly[j][1] - poly[i][1])):
                c = not c
            j = i
        return c

    def find_in_list(self,item_id, item_list):
        for x in item_list:
            if x['crate_id'] == item_id:
                print ("I found it!")
                return x

    ####################################################################
    # Load the coordinate system modules into self.coordinate_systems  #
    ####################################################################

    def load_coordinate_systems(self):
        # this could be implemented like acp_decoders
        sys.path.append("..")

        self.coordinate_systems = {}

        # William Gates Building
        from acp_coordinates.WGB import WGB
        self.coordinate_systems["WGB"] = WGB()
        print("Loaded coordinate system WGB")

        # IfM Building
        from acp_coordinates.IFM import IFM
        self.coordinate_systems["IFM"] = IFM()
        print("Loaded coordinate system IFM")

        # Lockdown Lab
        from acp_coordinates.LL import LL
        self.coordinate_systems["LL"] = LL()
        print("Loaded coordinate system LL")
