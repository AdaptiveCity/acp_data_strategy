from math import cos, radians

class InBuildingCoordinates:
    def __init__(self, system, lat_o, lng_o, dlat, dlng, dx, dy):
        self.system = system
        self.lat_o = float(lat_o)
        self.lng_o = float(lng_o)
        self.dlat = float(dlat)
        self.dlng = float(dlng)
        self.dx = float(dx)
        self.dy = float(dy)

    def getGPS(self, x, y, f, z):

        lat = self.lat_o + (y*self.dlat)/self.dy
        lng = self.lng_o + (x*cos(radians(lat))*self.dlng)/self.dx

        return lat, lng, f+z

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