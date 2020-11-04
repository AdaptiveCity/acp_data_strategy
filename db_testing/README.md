# json_db.sh

This is a utility to move AdaptiveCity sensor metadata and sensor_type metadata between JSON files and PostgreSQL.

In general the table is assumed to have the structure `identifier`, `timestamp updated`, `timestamp ended`, `json info`, e.g.
the `sensors` table below.

Records are added cumulatively to the table so that a record is kept of changes to a given sensor. This requires an `acp_ts`
to be included with the incoming data, and the previous record for that sensor (if it exists) will have that value set as
its `acp_ts_end`. The new record with have `acp_ts_end` as `NULL`.

Consequently, the basic `json_db.sh --dbread ...` which reads the database and outputs JSON is coded to only extract the lastest
record for each sensor / sensor_type, returned as a json object with the `acp_id` as property names. If the entire history is
required then the `json_db.sh --dbreadall ...` command can be used and the result will be a json list.

## install

(will be added to `acp_data_strategy` readme)

```
sudo apt install libpg-dev
```

As user `acp_prod` (database will default to `acp_prod`):

```
psql

CREATE TABLE public.sensors (
    acp_id character varying NOT NULL,
    acp_ts TIMESTAMP,
    acp_ts_end TIMESTAMP,
    sensor_info jsonb
);

```

```
source venv/bin/activate
python3 -m pip install psycopg2
```

## Command line usage of `json_db.sh`

```
json_db.sh
    --status
    --clear
    --dbread --dbtable <tablename> [--jsonfile <filename>] [--id <identifier>]
    --dbreadall --dbtable <tablename> [--jsonfile <filename>] [--id <identifier>]
    --dbwrite --dbtable <tablename> [--jsonfile <filename>]
    --dbmerge --dbtable <tablename> [--jsonfile <filename>]

## `json_db.sh --status --dbtable <tablename>`

Reports some general status of the given database table (e.g. number of rows, most recent update)

## `json_db.sh --clear --dbtable <tablename> [--id <identifier>]`

WARNING: removes rows from the table

If an identifier is given (i.e. an `acp_id` or `acp_type_id`) then only the records for that item will be removed.

## `json_db.sh --dbread --dbtable <tablename> [--jsonfile <filename>] [--id <identifier>`]

READS the database table, returning a json object with a property-per-sensor (or sensor_type)

If no `--jsonfile <filename>` is given, the command writes to stdout.

Note the table can contain multiple timestamped records with the same identifier and this command will return the most
recent in each case. I.e. for the `sensors` table then most recent sensor metadata will be returned for each sensor.

If an `--id` is given, then only the latest data for that identifier will be returned.

## `json_db.sh --dbreadall --dbtable <tablename> [--jsonfile <filename>] [--id <identifier>`]

Like `--dbread`, but returns **all** the records in the database table, not only the most recent for each
sensor / sensor_type.

Consequently the json returned is a *json list*, not a json object with a property-per-sensor/sensor_type.

## `json_db.sh --dbwrite --dbtable <tablename> [--jsonfile <filename>]

Kind-of the inverse of `--dbread`.

So for a given json file e.g. `sensors.json`, a `--dbwrite --jsonfile sensors.json` followed by `--dbread --jsonfile sensors2.json`
should result in `sensors.json` and `sensors2.json` having the same content.

## `json_db.sh --dbmerge --dbtable <tablename> [--jsonfile <filename>]`

This is similar to a `--dbwrite` **except** each the data from the `--jsonfile` will be **merged** with the corresponding object
in the database. This is useful if the new json contains a new property for existing sensors, e.g. `ttn_settings` so these can be
combined with exising properties such as `acp_location` which may alrady be recorded for the sensor.

Note that every 'base level` property in the `--jsonfile` will overwrite the existing property for the same object in the
database, i.e. this is not a recursive 'deep' merge.

# Accumulated background stuff

email ijl20 to Rohit 2020-10-14:

I'm in the process of doing something similar between the JSON files and postgresql to complete the acp_data_strategy work using the data from postgresql rather than the files (as you had it in the prior iteration of acp_data_strategy). I.e. see acp_data_strategy/db_testing and you'll see the work in progress.

I.e. the 'json' file format of our sensor and sensor_type data can act as a means of exchange of data between the database and TTN.

At the moment we have

acp_data_strategy/secrets/sensors.json
acp_data_strategy/secrets/sensor_types.json

both of which are JSON 'dictionaries' keyed on acp_id and acp_type_id respectively.

I am writing python/bash scripts that will import/export data from the tables from/to JSON files. I'll need to support multiple methods for file <-> database, but in principle these are similar to file <-> ttn, e.g. I'll have something like:
```
sensors_write.py <sensors json file name>:

              sensors json file -> WRITE each sensor object to sensors db table,
                                             overwrite if already there.

sensors_merge.py <sensors json file name>:
              sensors json file -> MERGE each sensor object into db table,
                                              keep existing properties if they're not overwritten

sensors_read <sensors json file name>:
              read all sensors from DB & export to (optional) JSON file / stdout

sensor_read <acp_id> <sensors json file name>:
             read a single sensor from DB, and write it into (optional, existing) sensors json file
             If the <sensor json file> isn't given, then write to stdout.

sensor_delete <acp_id>:
             deletes that sensor from the database
```
So pretty basic, but should form a useful set of scripts for the database (me) and TTN (you) with JSON files in the middle, and in due course we'll add the capability of going straight database <-> ttn but the file scripts will still be useful.
