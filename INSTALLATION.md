# acp_data_strategy installation

This is still a work-in-progress, using JSON files (e.g. BIM.json) as the source of the data. The 'production' version will
move that data back into Postgres.

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
cp ~acp_prod/nginx/includes2/cdbb_apis.conf /etc/nginx/includes2/
sudo nginx -t
sudo service nginx restart
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
