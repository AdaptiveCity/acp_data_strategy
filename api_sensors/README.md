# api_sensors

This is the API to access the sensor metadata.

The underlying information is stored as information-per-sensor and
information-per-sensor-type.

## /get/<acp_id>/[?metadata=true]

The canonical "get" api call, returns the sensor metadata for sensor with id "<acp_id>".
Given optional "?metadata=true", the API will also return the sensor *type* metadata.

Get the metadata for a given sensor (e.g. 'rad-ath-003d0f'), including the type metadata

## /get_bim/<coordinate_system>/<crate_id>/

Get sensors for a given crate_id, returning dictionary of sensors

## /get_floor_number/<coordinate_system>/<floor_number>/

Return sensors found on a given floor

## /get_gps/
DEBUG this API call **really** needs parameters (what info to show, lat/lng box?)
Get all sensors with a GPS location (i.e. lat/lng)

## /get_type/<acp_type_id>/'

Get the metadata for a given sensor TYPE (e.g. 'rad-ath')

## /list/
Return a list of sensors

We could support querystring filters e.g. '?feature=temperature'

Return a list of sensor's metadata

Returns { sensors: [..], types: [..]}

## /list_types/

Return a list of sensor types

We could support querystring filters e.g. '?feature=temperature'

Return a list of sensor type  metadata

Returns { types: { "elsys-ems": {...}, ... }}
