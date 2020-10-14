import json
import sys

from dbconn import DBConn

DEBUG = True

####################################################################
#
# Main
#
####################################################################

if __name__ == '__main__':
    print("sensors_load")

    with open('settings.json', 'r') as settings_file:
        settings_data = settings_file.read()

    # parse file
    settings = json.loads(settings_data)

    print("SENSORS API loaded settings.json")

    with open('test_sensors.json', 'r') as test_sensors:
        sensors_data = test_sensors.read()

    # parse file
    sensors = json.loads(sensors_data)

    print("SENSORS API loaded test_sensors.json")

    print(sensors)

    db_conn = DBConn(settings)

    for acp_id in sensors:
        query = ("INSERT INTO " + settings["TABLE_SENSORS"] +
                " (acp_id, sensor_info) VALUES ('" + acp_id + "','" + json.dumps(sensors[acp_id]) + "')")
        try:
            db_conn.dbwrite(query)
            print(query)
            flag = True
        except:
            if DEBUG:
                print(sys.exc_info())
