#!/usr/bin/env python3

import json
import sys

from dbconn import DBConn

DEBUG = True

####################################################################
# Write
####################################################################
def json_db_write(json_filename):
    with open(json_filename, 'r') as test_sensors:
        sensors_data = test_sensors.read()

    # parse file
    sensors = json.loads(sensors_data)

    print("loaded {}".format(json_filename))

    print(sensors)

    db_conn = DBConn(settings)

    for acp_id in sensors:
        query = ("INSERT INTO " + settings["TABLE_SENSORS"] +
                " (acp_id, sensor_info) VALUES ('" + acp_id + "','" + json.dumps(sensors[acp_id]) + "')")
        try:
            #db_conn.dbwrite(query)
            print(query)
            flag = True
        except:
            if DEBUG:
                print(sys.exc_info())

####################################################################
# Write
####################################################################
def json_db_read(json_filename):
    #with open(json_filename, 'r') as test_sensors:
    #    sensors_data = test_sensors.read()
    #
    # parse file
    #sensors = json.loads(sensors_data)
    #
    #print("loaded {}".format(json_filename))
    #
    #print(sensors)

    db_conn = DBConn(settings)

    for acp_id in sensors:
        query = ("SELECT * FROM " + settings["TABLE_SENSORS"] )
        try:
            db_conn.dbread(query)
            print(query)
            flag = True
        except:
            if DEBUG:
                print(sys.exc_info())

####################################################################
#
# Main
#
####################################################################

if __name__ == '__main__':
    print("json_db {} args",len(sys.argv))

    ######################
    # load settings.json
    ######################
    with open('settings.json', 'r') as settings_file:
        settings_data = settings_file.read()

    # parse file
    settings = json.loads(settings_data)

    print("loaded settings.json")

    #######################
    # execute command
    #######################
    if sys.argv[1] == "write":
        json_db_write(sys.argv[2])
    elif sys.argv[1] == "read":
        json_db_read(sys.argv[2])
