
# Building coordinate system
import math

DEBUG = True

# class WGB defines:
#    xyzf(building_coordinates) -> returns { x: y: z: f:} in meters / floor number (Ground=0)
#    gps(building_coordinates) -> returns { acp_lat, acp_lng, acp_alt }
#    f(building_coordinates) -> returns integer floor number
#    latlng( [x,y] ) -> returns [acp_lat, acp_lng] (where x,y are WGB coords)
#
# acp_location:
# { "system": "WGB",  // coordinate system identifier, always "WGB" for this system
#   "x": 123.4,       // local x value (arbitrary units)
#   "y": 567.8,       // local y value (arbitrary units)
#   "f": 1,           // floor number, 0 is Ground
#   "fz": 1.2         // height offset (m) from floor
# }
#

# import with:
# from classes.coordinates.WGB import WGB

# In general we refer to the in-building coordinates as "...building..."
# and the world coordinates (WGS84) as "...gps..."

class WGB(object):
    def __init__(self):
        if DEBUG:
            print("{} Building coordinate system".format(self.__class__.__name__))

        # In in-building system, which corner of the building is 0,0
        self.origin = "TOP_LEFT"

        # In GPS system, lat/lng of in-building 0,0 point
        self.origin_gps = { "acp_lat": 52.21136,
                            "acp_lng": 0.0916,
                            "acp_alt": 20 # I made this up
                          }

        # Scales used to convert building coordinates to meters
        self.scale = { "x": 0.12,
                       "y": -0.12,
                       "fz": 1.0
                     }
        # Offsets used to convert building coordinate heights to meters
        self.floor_m = [ 0.0, 4.0, 8.0, 12.0 ] # I.e. second floor is 8m above 0,0,0.

        # Amount building coords must be ROTATED CLOCKWISE to align +y = GPS North
        self.rotate = 15.0 #degrees

        # Store mapping of floor number to acp_location property name (needed?)
        self.floor_number = "f"

        # To speed up conversion to lat/lng, cache the rotation matrix
        # Note we could combine rotation and scaling into this (& use numpy)
        theta = math.radians(self.rotate)
        self.rotate_matrix = [ [ math.cos(theta), math.sin(theta) ],
                               [ -math.sin(theta), math.cos(theta) ] ]

    ######################################################################
    #  Class public api calls
    ######################################################################

    # Convert building coordinates to x,y,z,f  (xyz meters, f=floor#)
    # When rotated so +Y aligns with NORTH then +X will align EAST
    def xyzf(self, building_coordinates):
        return { "system": "XYZF",
                 "x": round(building_coordinates["x"] *  self.scale["x"],3),
                 "y": round(building_coordinates["y"] *  self.scale["y"],3),
                 "z": self.z(building_coordinates),
                 "f": building_coordinates["f"]
               }

    def building(self, xyzf):
        return { 
                "system": "WGB",
                 "x": round(xyzf["x"] /  self.scale["x"],3),
                 "y": round(xyzf["y"] /  self.scale["y"],3),
                 "zf": xyzf['z'],
                 "f": xyzf['f']
               }

    # Convert building coordinate to lat/lng
    # Input: building coordinates
    # Returns: { acp_lat, acp_lng, acp_alt }
    def gps(self, building_coordinates):
        xyzf = self.xyzf(building_coordinates)
        # rotate for x,y aligned to true North
        x = xyzf["x"] * self.rotate_matrix[0][0] + xyzf["y"] * self.rotate_matrix[0][1]
        y = xyzf["x"] * self.rotate_matrix[1][0] + xyzf["y"] * self.rotate_matrix[1][1]
        # lat = 111111 meters/degree
        lat = self.origin_gps["acp_lat"] + y / 111111 # latitude degrees (+ve = North)
        # lng = cos(lat) * 111111 meters/degree
        lng = self.origin_gps["acp_lng"] + x / (0.616 * 111111) # longitude degrees (+ve = East)
        alt = self.origin_gps["acp_alt"] + xyzf["z"] # altitude meters (+ve = Up)

        return { "acp_lat": lat, "acp_lng": lng, "acp_alt": alt }

    # Convert WGB [x,y] -> GPS [lat, lng]
    # Note this routine is different than others in accepting/returning [x, y] rather than building_coordinates
    def latlng(self, xy):
        # Create a temporary acp_location - we're only using x,y:
        acp_location_coords = {"x": xy[0], "y": xy[1], "f": 0, "fz": 0 }
        gps_coords = self.gps(acp_location_coords)
        return [ gps_coords["acp_lat"], gps_coords["acp_lng"] ]

    # Convert WGB [x,y] -> XYZF [x, y] (in meters, with +x -> +y anticlockwise)
    # Note this routine is different than others in accepting/returning [x, y] rather than building_coordinates
    def xy(self, xy):
        # Create a temporary acp_location - we're only using x,y:
        acp_location_coords = {"x": xy[0], "y": xy[1], "f": 0, "fz": 0 }
        xyzf_coords = self.xyzf(acp_location_coords)
        return [ xyzf_coords["x"], xyzf_coords["y"] ]

    # Return integer floor number, given building coordinates object
    def f(self, building_coordinates):
        return building_coordinates["f"]

    ######################################################################
    #  Support functions
    ######################################################################

    # Return z height in meters from 0,0,0, from building coordinates.
    def z(self, building_coordinates):
        # Get "fz" value (or 0)
        fz = building_coordinates["fz"] if "fz" in building_coordinates else 0
        return self.floor_m[building_coordinates["f"]] + fz
