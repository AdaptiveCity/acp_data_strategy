# acp_data_strategy installation

## Install Postgres and Setup Database

Install postgres:

```
sudo apt update
sudo apt install postgresql postgresql-contrib
```

Check the PostgreSQL database is running:
```
systemctl status postgresql
```
Also to check older versions of PostgreSQL are not still running:
```
ps aux | grep postgresql
```
If there are older versions running, use `dpkg -l | grep postgres` to see the packages involved and `sudo apt purge <package-name>`
to uninstall the old versions. Check `/etc/postgresql/<version>/main/postgresql.conf | grep port` to ensure PostgreSQL is accessible
via port 5432 (an alternative port can be used, but settings for PostgreSQL, acp_data_strategy API's, and acp_web need to be the
same.

See [this guide to setting up PostgreSQL for Django](https://www.digitalocean.com/community/tutorials/how-to-use-postgresql-with-your-django-application-on-ubuntu-14-04)

Change to postgres user (created by the postgres install):
```
sudo su - postgres
```
Start the `psql` console:
```
psql
```
At the `psql` prompt, create database & user `acp_prod`
```
CREATE DATABASE acp_prod;
```
Create user `acp_prod` and permit to use database (the password is in `acp_web/secrets/settings.py`):
```
CREATE USER acp_prod WITH PASSWORD '<password>';
ALTER ROLE acp_prod SET client_encoding TO 'utf8';
ALTER ROLE acp_prod SET default_transaction_isolation TO 'read committed';
ALTER ROLE acp_prod SET timezone TO 'Europe/London';
GRANT ALL PRIVILEGES ON DATABASE acp_prod TO acp_prod;
```
As the `acp_prod` user you can now test PostgreSQL access with:
```
psql
```
(Ctrl-D to quit)
```

To dump/restore a database from an existing server:

As user `acp_prod` on existing server:
```
pg_dump -c acp_prod >acp_prod_database_backup.sql
```
As use `acp_prod` on your new server:
```
psql acp_prod <acp_prod_data_backup.sql
```

If not restoring from another database, the `acp_data_strategy` tables can be created:

As the `acp_prod` user, command `psql` and:
```
CREATE TABLE sensors (
    record_id SERIAL,
    acp_id char(50) NOT NULL,
    acp_ts TIMESTAMP NOT NULL,
    acp_ts_end TIMESTAMP,
    sensor_info jsonb
);

CREATE TABLE sensor_types (
    record_id SERIAL,
    acp_type_id char(50) NOT NULL,
    acp_ts TIMESTAMP NOT NULL,
    acp_ts_end TIMESTAMP,
    type_info jsonb
);

CREATE TABLE bim (
    record_id SERIAL,
    crate_id char(50) NOT NULL,
    acp_ts TIMESTAMP NOT NULL,
    acp_ts_end TIMESTAMP,
    crate_info jsonb
);
```

## Just importing *data* from another system

As `acp_prod` user:

To backup the table contents on another system:
```
pg_dump acp_prod --data-only -t sensors >sensors_backup.sql
```
To restore that data:
```
psql acp_prod <sensors_backup.sql
```

## Configure the data API's

Change user to `acp_prod`.

```
cd ~
git clone https://github.com/AdaptiveCity/acp_data_strategy
cd acp_data_strategy
```

Copy the `secrets` directory from an existing acp_data_strategy installation (this contains the data `.json` files).

Now as the `acp_prod` user you should have `~/acp_data_strategy/secrets/`

As sudo user:
```
sudo cp ~acp_prod/acp_data_strategy/nginx/includes2/cdbb_apis.conf /etc/nginx/includes2/
sudo nginx -t
sudo service nginx restart
```

```
sudo apt install python3-dev
sudo apt install libpq-dev
```

As user `acp_prod`:

Create the required Python virtualenv:
```
python -m venv venv
source venv/bin/activate
python -m pip install pip --upgrade
python -m pip install wheel
python -m pip install -r requirements.txt
```

We are about to start the API's but first confirm the API's are NOT running:
```
./status.sh
```
Should display something like:
```
1601462319.877 api_bim      FAIL not running
1601462319.918 api_sensors  FAIL not running
1601462319.958 api_readings FAIL not running
1601462319.998 api_space    FAIL not running
```
As the `acp_prod` user, start the API's with:
```
cd ~/acp_data_strategy
./run.sh
```
You can re-check the running API's status with `./status.sh`.

To restart any api (with `api_bim`, `api_sensors`, `api_readings`, `api_space`), e.g. for `api_bim`:
```
cd ~/acp_data_strategy
./restart.sh api_bim
```

Test (bim) API with:
```
<servername>/api/bim/get/FE11/
```
You should see a Json return message with object properties.

If that fails, maybe the nginx configuration is wrong, check that by going to the api on `localhost` directly, either
via a browser if you are installing on a workstation with a GUI, or use `wget` from the command line on the server.
```
wget http://localhost:5010/get/FE11/
```
In case it has changed, the port used is defined in `acp_data_strategy/settings.json`.

## To launch on reboot

As `acp_prod` user:
```
crontab -e
```

Add line:
```
@reboot /home/acp_prod/acp_data_strategy/run.sh
```
