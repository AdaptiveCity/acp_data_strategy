#!/usr/bin/env python3

import json
import sys
import argparse

from dbconn import DBConn

DEBUG = True

####################################################################
# Import
####################################################################
def json_db_import(json_filename):
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
# Export
####################################################################
def json_db_export(json_filename):
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
# Load settings
####################################################################
def load_settings():
    with open('secrets/settings.json', 'r') as settings_file:
        settings_data = settings_file.read()

    # parse file
    settings = json.loads(settings_data)
    return settings

####################################################################
# Set up argument parsing
####################################################################

def parse_init():
    parser = argparse.ArgumentParser(description='Import/export json data <-> PostgreSQL')
    parser.add_argument('--jsonfile',
                        nargs='?',
                        metavar='<filename>',
                        help='JSON file for import or export')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--import',
                        action='store_true',
                        help='Import jsonfile -> PostgreSQL')
    group.add_argument('--export',
                        action='store_true',
                        help='Export PostgreSQL -> jsonfile (or stdout if no jsonfile)')
    return parser

####################################################################
#
# Main
#
####################################################################

if __name__ == '__main__':
    print("json_db {} args",len(sys.argv))

    parser = parse_init()
    args = parser.parse_args()

    print(args)
    
    settings = load_settings()

    print("loaded settings.json")

    #######################
    # execute command
    #######################
    if sys.argv[1] == "write":
        json_db_write(sys.argv[2])
    elif sys.argv[1] == "read":
        json_db_read(sys.argv[2])
