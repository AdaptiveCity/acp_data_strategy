#!/usr/bin/env python3

import argparse
import sys
import json

from classes.json_db import JsonDB

DEBUG = True


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
    group.add_argument('--dbmerge',
                        action='store_true',
                        help='Read records from jsonfile (or stdin if no jsonfile) and merge into matching PostgrSQL records')
    group.add_argument('--dbread',
                        action='store_true',
                        help='Export most recent PostgreSQL records -> jsonfile (or stdout if no jsonfile)')
    group.add_argument('--dbreadall',
                        action='store_true',
                        help='Export ALL records from PostgreSQL -> jsonfile (or stdout if no jsonfile)')
    return parser

####################################################################
#
# Main
#
####################################################################

if __name__ == '__main__':

    parser = parse_init()
    args = parser.parse_args()

    settings = load_settings()

    json_db = JsonDB(settings)

    # If --clear is requested, do this AS WELL as other options (e.g. --dbload)
    if args.clear:
        json_db.db_clear()

    # If --status is requested, do this AS WELL as other options
    if args.status:
        json_db.db_status()

    if args.dbread:
        json_db.db_read(args.jsonfile)
    elif args.dbreadall:
        json_db.db_readall(args.jsonfile)
    elif args.dbwrite:
        json_db.db_write(args.jsonfile)
    elif args.dbmerge:
        json_db.db_merge(args.jsonfile)
