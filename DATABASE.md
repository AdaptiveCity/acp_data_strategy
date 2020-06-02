# The ACP Database

Name: acp_prod

## Tables
### sensors
This table stores the metadata information of all the sensors being deployed. It has two columns;
+ acp_id (VARCHAR): This is the unique id given to each of the deployed sennsors.
+ sensor_info (jsonb): This column stores all the information of the sensor. As different category of sensors could have specific metadata information unique to itself, we opted for a jsonb type.

Example Rows:

|      acp_id      |                                                                  sensor_info                                                                 |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| adeunis-test-3  | {"ts": 1589469825.165538, "type": "RF", "owner": "ijl20","source": "mqtt_ttn","features": "battery, button, downlink_counter, gps_reception, gps_satellites, latitude, longitude, rssi, snr, temperature, uplink_counter", "acp_location": {"system": "GPS","acp_alt": 10,"acp_lat": 52.2108765,"acp_lng": 0.0912775},"parent_crate_id": "FF"} |
| elsys-co2-041ba9 | {"ts": 1589469979.861816,"type": "co2","owner": "ijl20","source": "mqtt_ttn","features": "co2, humidity, light, motion, temperature, vdd","acp_location": {"system": "GPS","acp_alt": 10,"acp_lat": 52.2108765,"acp_lng": 0.0912775},"parent_crate_id": "FN05"} |

In the above example the sensor_info field includes;
+ acp_ts: The Unix timestamp when the metadata was stored. Owing to the fact that the location could change later we have opted to include timestamp.
+ type: type of sensor
+ owner: the owner of the device
+ source: the mqtt source which is publishing the messages from the sensor
+ features: set of features of which the sensor logs information of
+ acp_location: The location of the sensor. This could be either inside a building in which case we use building specific system like WGB and (x,y,f,z). This system could be mapped to a latitude, longitude and altitude system and vice-versa.
+ parent_crate_id: The crate in BIM in which this sensor is included.

### bim
This sensor stores the BIM information for all the buildings under ACP based on the Object-level hierarchy. Each of the object in this table is represented as a crate which may or may not have child or parent crates. It has two columns;
+ crate_id (VARCHAR) - The unique id of the building component.
+ bim_info (VARCHAR) - Same as the sensors table, this column stores all the information of the crate.

Example Rows:

|      crate_id      |                                                                  bim_info                                                                 |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| WGB  | {"acp_ts": 1589469825.165538, "long-name": "William Gates Building","crate_type": "building","description": "Crate Description","acp_boundary": "{0,0,0,78,73,78,73,0}","parent_crate_id": "West Cambridge"} |
| FF | {{"acp_ts": 1589469825.165538,"long-name": "First Floor","crate_type": "floor","description": "First floor of WGB","acp_boundary": "{0,0,0,78,73,78,73,0}","parent_crate_id": "WGB"} |
| FN15 | {"acp_ts": 1589469825.165538,"long-name": "FN15","crate_type": "room","description": "FN15 on FF","acp_boundary": "{35,68,35,73,40,73,40,73,38,70,38,68}","parent_crate_id": "FF"} |

In the above example the bim_info field includes;

+ acp_ts - The Unix timestamp when the metadata was stored.
+ long-name - Long name if any of the crate.
+ crate_type - Type of the crate.
+ description - Crate description.
+ acp_boundary - This attribute stores the coordinates of the vertices of the polygon forming the object. Any object would be mapped to a polygon having each vertex corresponding to the In-building coordinate of the building this crate belongs to. The standard being to start from the vertex on the leftmost lower corner of the object and then moving counter-clockwise. Format is of the form {x1, y1, x2, y2, ...}.
+ parent_crate_id - The crate in BIM in which this crate is included.