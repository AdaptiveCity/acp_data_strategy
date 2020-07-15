
from os import listdir, path
import json
from collections import defaultdict
import sys
from datetime import datetime
import time
from flask import request
import requests
# NOTE we also have "load_coordinate_systems()" which will import modules from acp_coordinates

DEBUG = True

###################################################################
#
# BIM DataAPI
#
###################################################################

BIM=None

class DataAPI(object):

    def __init__(self, settings):
        global BIM
        print("Initializing BIM DataAPI")
        self.settings = settings
        BIM = self.load_BIM()
        print("{} loaded".format(settings["bim_file_name"]))
        self.load_coordinate_systems()

    #####################################################################
    #  METHODS CALLED FROM API                                          #
    #####################################################################

    #takes in crate_id and depth and returns all children of that crate
    def get_bim_tree(self, crate_id, depth):
        global BIM

        if DEBUG:
            print("get_bim_tree {} {}".format(crate_id,depth))

        # Get list  of children of the desired crate to required depth
        crates = self.get_tree(crate_id, int(depth))

        if crates is None:
            return ""

        return json.dumps(crates)

    #takes in floor number and returns all room/corridor crates that have acp_location[f]==floor
    def get_floor_number(self, coordinate_system,floor_number):
        global BIM

        crates = []
        # coords.f(acp_location) will return floor number
        coords = self.coordinate_systems[coordinate_system]

        #get all WGB children (we retrieve all building children because some children can be spanning several floors)
        for crate_id in BIM:
            crate = BIM[crate_id]
            if "acp_location" in crate:
                loc = crate["acp_location"]
                if loc["system"] == coordinate_system and coords.f(loc) == int(floor_number):
                    crates += [ crate ]

        self.add_xyzf(crates)

        return json.dumps(crates)

    # Return the BIM object with additional properties (if they don't already exist):
    #     acp_lat, acp_lng, acp_alt
    #     acp_boundary_gps with x,y coordinates as
    #DEBUG api_bim.py get_gps depth not implemented - maybe we don't need it
    def get_gps(self, crate_id, depth):
        if crate_id not in BIM:
            return "[]"
        crate = BIM[crate_id]
        if "acp_location" not in crate:
            # We need acp_location to for the coordinate system
            return "[]"
        coordinate_system = crate["acp_location"]["system"]
        if "acp_boundary" in crate and "acp_boundary_gps" not in crate:
            crate["acp_boundary_gps"] = self.acp_boundary_to_gps(coordinate_system, crate["acp_boundary"])
        #DEBUG api_bim.py get_gps not implemented acp_lat, acp_lng, acp_alt
        return json.dumps([crate])

    # Return the BIM object with additional properties (if they don't already exist):
    #     acp_boundary_xyz with x,y coordinates in anticlockwise, meters units
    #DEBUG api_bim.py get_gps depth not implemented yet
    def get_xyzf(self, crate_id, depth):
        # Get list  of children of the desired crate to required depth
        crates = self.get_tree(crate_id, int(depth))

        self.add_xyzf(crates)

        if crates is None:
            return ""

        return json.dumps(crates)

    ###########################################################################
    #
    # Support functions
    #
    ###########################################################################

    # Load ALL the BIM data from the store (usually data/BIM.json)
    def load_BIM(self):
        file_name=self.settings["bim_file_name"]

        #load BIM.json and create dict
        with open(file_name,'r') as json_file:
            #WGB= json.loads(json_file.read())
            BIM_data=json.load(json_file)['crates']
        print(file_name," loaded successfully")
        return BIM_data

    # Update a list of creates with "acp_location_xyz" and "acp_boundary_xyz" properties
    def add_xyzf(self, crates):
        if crates is None:
            return

        for crate in crates:
            if "acp_location" not in crate:
                # We need acp_location to for the coordinate system
                return # exit with crates unchanged
            acp_location = crate["acp_location"]
            coordinate_system = acp_location["system"]
            # Note the xyz coordinates may already be cached in the bim data
            if "acp_location_xyz" not in crate:
                crate["acp_location_xyz"] = self.coordinate_systems[coordinate_system].xyzf(acp_location)
            if "acp_boundary" in crate and "acp_boundary_xyz" not in crate:
                crate["acp_boundary_xyz"] = self.acp_boundary_to_xy(coordinate_system, crate["acp_boundary"])

        return

    #Compares crate_id with parent_id and determines if it's a match
    #is_child(POTENTIAL_CHILD, PARENT)
    def is_child(self, child,  parent_crate_id):
        child_id  = child['crate_id']
        parent_id = child['parent_crate_id']

        result = parent_id == parent_crate_id

        return result

    # return a list of immediate children of this crate
    def get_children(self, parent_id):
        #iterate through the BIM and determine if parent
        #has any children
        children = []
        for crate_id in BIM:
            crate = BIM[crate_id]
            if (self.is_child(crate, parent_id)):
                if DEBUG:
                    print("get_children adding child: {}".format(crate_id))
                children += [ crate ]

        return children

    # Return list of crates by flattening tree from crate_id down
    def get_tree(self, crate_id, depth):

        if DEBUG:
            print("get_tree",depth,crate_id)

        try:
            crate_list = [ BIM[crate_id] ]
        except KeyError:
            return []

        if depth > 0:
            children = self.get_children(crate_id) # returns list of immediate-child crate objects

            remaining_depth = depth - 1

            for child in children:
                crate_list += self.get_tree(child["crate_id"], remaining_depth)

        return crate_list

    ####################################################################
    ### In-Building coordinate system -> GPS coords                 ###
    ####################################################################

    # Convert the building coords boundaries into equivalent latlngs
    # acp_boundary is a list [{ boundary_type, boundary: [...] }...]
    def acp_boundary_to_gps(self, coordinate_system, acp_boundary):
        gps_boundaries = [] # this is the list we will return when completed
        for boundary_obj in acp_boundary:
            # create new gps_boundary object, with type set as original
            gps_boundary = { "boundary_type": boundary_obj["boundary_type"] }
            # add the latlng points to this object
            gps_boundary["boundary"] = self.points_to_gps(coordinate_system, boundary_obj["boundary"])
            # append this new object to the list
            gps_boundaries.append(gps_boundary)

        return gps_boundaries

    def points_to_gps(self, coordinate_system, points):
        gps_points = []
        for point in points:
            gps_point = self.point_to_gps(coordinate_system, point)
            gps_points.append(gps_point)

        return gps_points

    def point_to_gps(self, coordinate_system, point):
        return self.coordinate_systems[coordinate_system].latlng(point)

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
