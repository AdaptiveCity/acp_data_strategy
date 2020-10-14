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
