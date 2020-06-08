from math import cos, radians

class InBuildingCoordinates:
    def __init__(self, system, lat_o, lng_o, dlat, dlng, dx, dy):
        # The coordinate system being followed
        self.system = system
        # The latitude value corresponding to the origin
        self.lat_o = float(lat_o)
        # The longitude value corresponding to the origin
        self.lng_o = float(lng_o)
        # Difference between the latitute of the selected coordinates in the building
        self.dlat = float(dlat)
        # Difference between the longitude of the selected coordinates in the building
        self.dlng = float(dlng)
        # The total length between the selected points on the building along x-axis
        self.dx = float(dx)
        # The total length between the selected points on the building along y-axis
        self.dy = float(dy)

    # Returns the latitude, longitude and altitude corresponding to the inbuilding coordinates
    def getGPS(self, x, y, f, z):

        lat = self.lat_o + (y*self.dlat)/self.dy
        lng = self.lng_o + (x*cos(radians(lat))*self.dlng)/self.dx

        return lat, lng, f+z

    # Returns the inbuilding coordinates corresponding to the global coordinates
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