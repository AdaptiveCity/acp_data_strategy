The database of the Adaptive City Program. (This is a work in progress and would be updated in due course.)

## Database Name: postgres

## Tables
### metadata
This table stores the metadata information of all the sensors being deployed. It has two columns as of now;
+ acp_id (VARCHAR): This is the unique id given to each of the deployed sennsors.
+ info (jsonb): This currently stores all the information of the sensor. As different category of sensors could have specific metadata information unique to itself, we opted for a jsonb type.

Example Rows:

|      acp_id      |                                                                  info                                                                 |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| avatar-test-001  | {"acp_ts": "1585138617", "type": "smartplug", "owner": "rv355", "location": {"x": "2131.33", "y": "53272.22", "z": "1", "system": "WGB"}} |
| aoycocr-test-001 | {"acp_ts": "1585138617", "type": "smartplug", "owner": "jb2328", "location": {"x": "2654.33", "y": "53432.22", "z": "1", "system": "WGB"}} |
| gosund-test-001  | {"acp_ts": "1585138617", "type": "smartplug", "owner": "mrd45", "location": {"x": "2664.33", "y": "53432.22", "z": "1", "system": "WGB"}}  |

In the above example the info field includes;
+ acp_ts: The Unix timestamp when the metadata was stored. Owing to the fact that the location could change later we have opted to include timestamp.
+ type: type of sensor
+ owner: the owner of the device
+ location: The location of the sensor. This could be either inside a building in which case we use building specific system like WGB and (x,y,z). This system could be mapped to a latitude, longitude and altitude system and vice-versa.