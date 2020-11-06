#!/usr/bin/env python3

import argparse
import sys
import json

from classes.db_manager import DBManager

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
    parser.add_argument('--dbtable',
                        nargs='?',
                        metavar='<tablename>',
                        default='sensors',
                        help='Name of PostgreSQL table e.g. "sensors", "sensor_types".')
    parser.add_argument('--id',
                        nargs='?',
                        metavar='<identifier>',
                        help='Identifier to limit the scope e.g. (for --tablename sensors) "elsys-eye-044504".')
    parser.add_argument('--clear',
                        action='store_true',
                        help='ERASE all data from sensors table')
    parser.add_argument('--status',
                        action='store_true',
                        help='Report status of sensors table')
    command_group = parser.add_mutually_exclusive_group()
    command_group.add_argument('--dbwrite',
                        action='store_true',
                        help='Import jsonfile -> PostgreSQL')
    command_group.add_argument('--dbmerge',
                        action='store_true',
                        help='Read records from jsonfile (or stdin if no jsonfile) and merge into matching PostgrSQL records')
    command_group.add_argument('--dbread',
                        action='store_true',
                        help='Export most recent PostgreSQL records -> jsonfile (or stdout if no jsonfile)')
    command_group.add_argument('--dbreadall',
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

    db_manager = DBManager(settings)

    # Convert the --dbtable <tablename> into settings object e.g.
    # { "table_name": "sensors", "id": "acp_id", "info": "sensor_info" }
    dbtable = None
    if args.dbtable:
        dbtable = settings["TABLES"][args.dbtable]

    # If --clear is requested, do this AS WELL as other options (e.g. --dbload)
    if args.clear:
        db_manager.db_clear(dbtable, args.id)

    # If --status is requested, do this AS WELL as other options
    if args.status:
        db_manager.db_status(dbtable, args.id)

    if args.dbread:
        db_manager.db_read(args.jsonfile, dbtable, args.id)
    elif args.dbreadall:
        db_manager.db_readall(args.jsonfile, dbtable, args.id)
    elif args.dbwrite:
        db_manager.db_write(args.jsonfile, dbtable)
    elif args.dbmerge:
        db_manager.db_merge(args.jsonfile, dbtable)
