import time
from datetime import datetime

class Utils:
    @staticmethod
    def date_to_path(selecteddate):
        data = selecteddate.split('-')
        return(data[0]+'/'+data[1]+'/'+data[2]+'/')

    @staticmethod
    def date_to_sensorpath(selecteddate):
        data = selecteddate.split('-')
        return(data[0]+'/'+data[1]+'/')

    @staticmethod
    def date_to_sensorpath_name(selecteddate):
        data = selecteddate.split('-')
        return(data[0]+'-'+data[1]+'-'+data[2])

    ##past date so I could do tests without being connected to cdbba
    @staticmethod
    def getDateToday():
        dt = datetime.now()
        return dt.strftime("%Y-%m-%d")
        #return '2020-04-20'

    @staticmethod
    def getTimestampDate():
        dt = datetime.now()
        return str(time.time())+dt.strftime("_%Y-%m-%d-%H-%M-%S")

    @staticmethod
    def getTimestamp():
        return str(time.time())

    @staticmethod
    def getISO8601():
        return str(datetime.now().isoformat())
