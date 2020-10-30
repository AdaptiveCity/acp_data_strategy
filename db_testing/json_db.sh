#!/usr/bin/env python3

import json
import sys
import argparse

from dbconn import DBConn

DEBUG = True

####################################################################
# Clear database
####################################################################
def db_clear():
    db_conn = DBConn(settings)

    query = ("DELETE FROM " + settings["TABLE_SENSORS"] )
    db_conn.dbwrite(query)

####################################################################
# Report database status
####################################################################
def db_status():
    db_conn = DBConn(settings)

    query = ("SELECT COUNT(*) FROM " + settings["TABLE_SENSORS"] )
    rows = db_conn.dbread(query)
    print("rows in {} {}".format(settings["TABLE_SENSORS"],rows))

####################################################################
# Import JSON -> Database
####################################################################
def db_write(json_filename):
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
            db_conn.dbwrite(query)
            #print(query)
            flag = True
        except:
            if DEBUG:
                print(sys.exc_info())

####################################################################
# Export database -> JSON
####################################################################
def db_read(json_filename):
    #with open(json_filename, 'r') as test_sensors:
    #    sensors_data = test_sensors.read()
    #
    # parse file
    #sensors = json.loads(sensors_data)
    #
    #print("loaded {}".format(json_filename))
    #
    #print(sensors)

    outfile = open(json_filename,'w') if json_filename is not None else sys.stdout

    db_conn = DBConn(settings)

    query = ("SELECT * FROM " + settings["TABLE_SENSORS"] )
    try:
        rows = db_conn.dbread(query)
        print(rows)
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
    parser.add_argument('--clear',
                        action='store_true',
                        help='ERASE all data from sensors table')
    parser.add_argument('--status',
                        action='store_true',
                        help='Report status of sensors table')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--dbwrite',
                        action='store_true',
                        help='Import jsonfile -> PostgreSQL')
    group.add_argument('--dbread',
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

    # If --clear is requested, do this AS WELL as other options (e.g. --dbload)
    if args.clear:
        db_clear()

    # If --status is requested, do this AS WELL as other options
    if args.status:
        db_status()

    if args.dbread:
        db_read(args.jsonfile)
    elif args.dbwrite:
        db_write(args.jsonfile)
