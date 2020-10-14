# sensors / sensor_types move back into database


```
sudo apt install libpg-dev
```

As user `acp_prod` (database will default to `acp_prod`):

```
psql

CREATE TABLE public.sensors (
    acp_id character varying NOT NULL,
    sensor_info jsonb
);

CREATE TABLE public.sensor_types (
    acp_type_id character varying NOT NULL,
    sensor_type_info jsonb
);
```

```
source venv/bin/activate
python3 -m pip install psycopg2
```

I'm in the process of doing something similar between the JSON files and postgresql to complete the acp_data_strategy work using the data from postgresql rather than the files (as you had it in the prior iteration of acp_data_strategy). I.e. see acp_data_strategy/db_testing and you'll see the work in progress.

I.e. the 'json' file format of our sensor and sensor_type data can act as a means of exchange of data between the database and TTN.

At the moment we have

acp_data_strategy/secrets/sensors.json
acp_data_strategy/secrets/sensor_types.json

both of which are JSON 'dictionaries' keyed on acp_id and acp_type_id respectively.

email ijl20 to Rohit 2020-10-14:

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
