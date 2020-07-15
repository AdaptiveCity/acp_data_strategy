
from os import listdir, path
import json
from collections import defaultdict
import sys
from datetime import datetime
import time
from flask import request

import requests
from requests.exceptions import HTTPError

DEBUG = False

###################################################################
#
# DataAPI
#
# /gps_coords       - gives latitide, longitude positions of sensors
# /sensor_data       - gives in-building locations of sensors
# /room_list       - returns a list of object IDs from GF/FF/SF SVGs
# /BIM_WGB        - loads (or generates) data for /BIM_[GF/SF/FF]
# /BIM_GF          - loads GF json data from /BIM_WGB and generates an SVG of it
# /BIM_FF          - loads FF json data from /BIM_WGB and generates an SVG of it
# /BIM_SF          - loads SF json data from /BIM_WGB and generates an SVG of it
# /data            - ???
# /generate_bim    - ???

###################################################################

#r = requests.get('https://api.github.com/repos/psf/requests')
#r.json()["description"]

class DataAPI(object):

    def __init__(self,settings):
        print("Initializing SPACE DataAPI")
        self.settings = settings

    # This is the main call used by a web page requesting the SVG for a BIM object
    # Get SVG for a crate and its children
    # Will call the BIM API/get_xyz/crate_id/children
    def get_crate_svg(self, crate_id, children):
        print("data_api get_crate_svg",crate_id, children)
        #the following fails to return the right floorplan for FF (specifically GW20/GW23)
        bim_api_url = self.settings["API_BIM"]+"get_xyz/"+crate_id+"/"+str(children)+"/"
        return self.get_svg(bim_api_url)

    # Get SVG for a FLOOR, e.g. 'FF'
    def get_floor_svg(self,crate_id):
        bim_api_url = self.settings["API_BIM"]+"get/"+crate_id+"/1/"
        return self.get_svg(bim_api_url)

    # This functions returns every crate based on floor number,
    # specificaly [f] parameter in [acp_loc]
    def get_floor_number(self, coordinate_system, floor_number):
        #/api/bim/get_floor_number/<floor_number>
        bim_api_url = self.settings["API_BIM"]+'get_floor_number/'+coordinate_system+'/'+str(floor_number)+"/"
        return self.get_svg(bim_api_url)

    # Given a BIM API url, collect BIM crates and transform to SVG
    def get_svg(self, bim_api_url):
        #fetch data from BIM api
        try:
            response = requests.get(bim_api_url)
            response.raise_for_status()
            # access JSON content
            bim_objects = response.json()
        except HTTPError as http_err:
            print(f'space_api.py HTTP GET error occurred: {http_err}')
            exit(1)
        except Exception as err:
            print(f'space_api.py Other GET error occurred: {err}')
            exit(1)

        #children=self.get_children(BIM[crate]['crate_id'],[],depth)
        print("space_api get_svg bim objects list loaded", bim_objects)

          #elements required to create an XML SVG file
        svg_start = """<?xml version="1.0" encoding="utf-8"?>
        <svg version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" xml:space="preserve">
        """

        CRATE_BEGIN = """<g class="crate">
        """
        CRATE_END = """</g>
        """
        polygon_begin="""        <polygon id='"""
        polygon_mid=""" points='"""
        polygon_end="""'/>
        """

        crate_chunk = ''

        svg_BIM_open="""<g id='bim_request'>
        """
        svg_BIM_close="""</g>
        """
        svg_end="""
    </svg>
        """

        #parse the loaded json file and transform all location data into SVG polygons
        for crate in bim_objects:
            point_list=''

            crate_id = crate['crate_id']

            for pairs in crate['acp_boundary_xyz'][0]['boundary']:
                # Note y is NEGATIVE for XYZF (anti-clockwise)-> SVG (clockwise)
                point_list += str(pairs[0]) + "," + str(-pairs[1]) + " "
                #point_list+=list(map(str,pairs))[0]+","+list(map(str,pairs))[1]+" "

            #DEBUG this is assuming WGB coordinate system f === floor_number (can fix in <coordinate_system>.py)
            floor_number = crate['acp_location']['f'] # maybe we will make this acp_floor_number in XYZ system.

            polygon_crate_type="""' data-crate_type='"""+crate['crate_type']+"'"
            polygon_parent=""" data-parent_crate_id='"""+crate['parent_crate_id']+"'"
            polygon_floor_number = """ data-floor_number='""" + str(floor_number) + "'"

            #long name property may not exist for all crates
            try:
                polygon_long_name=""" data-long_name='"""+crate['long_name']+"'"
            except:
                polygon_long_name=" "

            #combine everything into a single polygon data object
            polygon_data = polygon_crate_type + polygon_long_name + polygon_parent + polygon_floor_number
            #polygon_data="'"

            #a list of all rooms on that floor wrapped in polygon tags
            polygon_chunk = polygon_begin + crate_id + polygon_data + polygon_mid + point_list + polygon_end

            crate_chunk += CRATE_BEGIN + polygon_chunk + CRATE_END

        #+circle_chunk
        #combine all chunks into a single SVG file with proper begining/endings tags
        final_svg = svg_start + svg_BIM_open + crate_chunk + svg_BIM_close + svg_end
        print("space_api get_svg returning\n{}".format(final_svg))
        return final_svg

    ##NEW API FUNCTION
    def get_sensors_count(self, crate_id, depth):
        crate=BIM[crate_id]
        #get children of the desired crate
        children=self.get_children(crate_id,[],depth)

        #if we get all children floors appear on the same level as rooms,
        #so perhaps it would be a good idea to remove them
        #by calling get_children(depth-1) and substracting results
        #from get_children(depth) (depth=2)

        #if no children,then return the crate itself
        if(len(children)<1):
            children=[]
            children.append(crate_id)

        responses=[]

        for child in children:

            #initiate the sensor counter
            counter=0

            #retrieve crate boundary, floor and type
            #since it's used to reference what crate
            #sensors belong to

            boundary=BIM[child]['acp_boundary'][0]['boundary']
            child_floor=BIM[child]['acp_location']['f']
            child_type=BIM[child]['crate_type']

            json_response={}
            json_response['crate_id']=child

            for sensor in SENSORS:
                #acquire location data for x,y and floor
                x_loc=SENSORS[sensor]['acp_location']['x']
                y_loc=SENSORS[sensor]['acp_location']['y']
                sensor_floor=SENSORS[sensor]['acp_location']['f']

                #determine the type of child to check what sensors belong to it
                if child_type=='room' or child_type=='floor':
                    #for rooms and floors we have to take into account the level at which sensors are
                    #deployed, since x/y for different floors overlap
                    if(self.is_point_in_path(x_loc,y_loc,boundary) and sensor_floor==child_floor):
                        counter+=1

                if(child_type=='building'):
                    if(self.is_point_in_path(x_loc,y_loc,boundary)):
                        counter+=1

                json_response['sensor']=counter
            responses.append(json_response)
        return {'data':responses}#{'crate':crate_id, 'sensors':counter}

    #NEW API FUNCTION
    #returns sensors readings in X crate
    def get_sensor_readings_in(self,crate):
        sensors={}

        workingDir = self.settings["base_path"]+'mqtt_ttn/sensors'

        print("request data")
        print(crate,"\n")
        depth=999#retrieves all children
        children=self.get_children(BIM[crate]['crate_id'],[],depth)
        print("children list loaded")

        #or perhaps it would be better to modify to return itself
        #if no children exist
        if len(children)<1:
            children.append(BIM[crate]['crate_id'])
            print("\nno children, just\n", children)

        for sensor in SENSORS:
            print('sensor',sensor)
            sensor_dict={}
            for child in children:
                print('child',child, "sensor crate",SENSORS[sensor]['acp_location']['crate_id'])
                if SENSORS[sensor]['acp_location']['crate_id']==child:
                    sensor_dict['sensor_id']=sensor
                    sensor_dict['acp_location']=SENSORS[sensor]['acp_location']

                    sensor_dict['readings']=self.get_recent_readings(sensor)

                    sensors[sensor]=sensor_dict

        return json.dumps({crate:sensors})


    ###########################################
    ## EVERYTHING BELOW THIS WILL BE DELETED ##
    ## (except Support Functions, of course) ##
    ###########################################

    #DEBUG this function needs parameters or renaming
    #DEBUG sensor_gps_coords() ??
    def get_sensors_latlng(self):
        #response['data'].append({'sensor':sdir,
        #    'acp_ts':jdata['acp_ts'],
        #    'latitude':jdata['metadata']['gateways'][0]['latitude'],
        #    'longitude':jdata['metadata']['gateways'][0]['longitude']
        #})
        #DEBUG mockup
        json_response = """
            { "sensors": [ { "sensor": "ijl20-sodaq-ttn",
                          "acp_ts": "1591094324.123",
                          "acp_lat": 52.210927,
                          "acp_lng": 0.092740,
                          "description": "Outside FE11"
                        }
                      ]
            }
        """
        print("gps_coords returning {}".format(json_response))
        return json_response


    ###########################################################################
    #
    # Support functions
    #
    ###########################################################################

    #https://en.wikipedia.org/wiki/Centroid#Of_a_polygon
    def get_centroid(self, polygon):
        def get_area(a):
            sigma=0
            for i in range(0, len(a)):
                # vertex ( xn, yn ) is assumed to be the same as ( x0, y0 )
                if((i+1)==len(a)):
                    i_=0
                else:
                    i_=i+1

                x =a[i ][0]
                x_=a[i_][0]

                y =a[i ][1]
                y_=a[i_][1]

                sigma+=(x*y_-x_*y)
            return 0.5*sigma

        def multiply(a):
            x_sum=0
            y_sum=0
            for i in range(0, len(a)):
                # vertex ( xn, yn ) is assumed to be the same as ( x0, y0 )
                if((i+1)==len(a)):
                    i_=0
                else:
                    i_=i+1

                x =a[i ][0]
                x_=a[i_][0]

                y =a[i ][1]
                y_=a[i_][1]

                x_sum+=(x+x_)*(x*y_-x_*y)
                y_sum+=(y+y_)*(x*y_-x_*y)

            return x_sum,y_sum

        multiply_x, multiply_y=multiply(polygon)
        area=get_area(polygon)

        cx=(1/(6*area))*multiply_x
        cy=(1/(6*area))*multiply_y

        return (round(cx,2),round(cy,2))

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

    #Compares crate_id with parent_id and determines if it's a match
    #is_parent(POTENTIAL_CHILD, PARENT)
    def is_parent(self,obj1, obj2):
        child_id       =obj1['crate_id']
        child_parent_id=obj1['parent_crate_id']

        parent_id=obj2['crate_id']

        result=child_parent_id==parent_id
        if DEBUG:
            print("is ", parent_id, "parent of ", obj1['crate_id'], "?",result )

        return result

        #A recursive function that retrieves all children from the BIM model and
        #using breadth first search
    def get_children(self,crate_object_id,out_list,depth):
        #temp list for first-level children
        temp_list=[]

        if DEBUG:
            print("\nInput",crate_object_id,"\n")

        p=BIM[crate_object_id] #parent

        #iterate through the BIM and determine if parent
        #has any children
        for crate in BIM:
            c=BIM[crate]    #child
            if (self.is_parent(c,p)):
                temp_list.append(c['crate_id'])

        #we now we checked one level down at this point
        #so decrease depth
        depth-=1

        #if parent has no children or wanted depth reached
        #return list and stop recursion from happening
        if len(temp_list)==0 or depth<0:
            return out_list

        #otherwise keep going down
        else:
            #append parent children to the main list and keep checking
            out_list+=temp_list
            for child in temp_list:
                #recursive loop for children of parent object
                self.get_children(BIM[child]['crate_id'],out_list,depth)

        return out_list

    #takes in a nested dict structure and returns a flat list
    #pass a dictionary and an empty list to use
    #e.g. list=nest_to_flat(dict, [])
    def nested_to_flat(self,dictionary, out_list):
        for keys in list(dictionary):
            #if DEBUG:
            #    print(keys, dictionary[keys])

            out_list.append(keys)

            #Empty dictionaries evaluate to False in Python:
            if bool(dictionary[keys]):
                self.nested_to_flat(dictionary[keys],out_list)

        return out_list
