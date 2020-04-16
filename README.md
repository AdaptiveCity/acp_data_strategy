# Adaptive City Program sensor metadata

This repo is intended to pull together the multiple approaches we're taking to normalize
the data coming in from our various sensors and sources.  This does *not* mean we assume
some miraculous uber-standard will magically make all the data sources adhere to common
protocols and formats. Rather, we are assuming the data will continue to be tailored to
each source and consequently be fairly diverse and we will take steps *where appropriate*
to make the data manageable.

## Summary of our approach

1. We propagate the data around our platform using JSON objects. This provides readability
plus essential flexibility in the data format.

2. We are likely to annotate the data with *additional* data properties (such as a normalized
sensor identifier property) but this is provided *as well as* whatever was in the data before,
rather than replacing it.

3. Where possible we enhance or normalize the data as far *upstream* as possible.
The Adaptive City Platform has a data-flow architecture with much processing in real-time
from the original sensor inputs to derived calculations, storage and visualization downstream. We
aspire to have much of the processing downstream independent of the specifics of the original
source. For example, producing a time vs. scalar chart of some data reading does not itself need
to understand the complexities of the data source.

4. Some properties are common to the majority of sensor data and we are seeking to normalize these
first. These include:
    * sensor identifier
    * timestamp most relevant to the data reading
    * location of the sensor
    * the confidence or reliability of the reading

In addition we may be able to generalize *some* of the data payload, for example by noting
that a for a given sensor or sensor type a `co2` reading in units `parts-per-million` is
available in sensor data property `payload_decoded > readings > co2`.

There are two significant platform elements relevant to our approach:

1. `acp_decoders`: a real-time component part of the
[acp_local_mqtt](https://github.com/AdaptiveCity/acp_local_mqtt) project, which subscribes to
incoming data and allows the dynamic addition of *decoders* capable of extracting and normalizing
key properties such that the annotated data can be re-published for consumption further
downstream like any other real-time data source.

2. The `ACP sensor metadata database` (documented below) which acts as a repository for
persistent metadata regarding the sensors which is accessible via an API for any process
during the data flow. For example this includes the `location` of the non-moving sensors.

## Time

`acp_ts` is intended for the property containing the timestamp most relevant to the sensor
data reading, containing the floating point seconds in epoch stored in a string. For example:
```
"acp_ts": "1586461606.465372"
```

Sensors designed within the project will include `acp_ts` in their transmitted data as the 
definitive time of the sensor reading, along with other timestamps from the internal processes of
the sensor.

Sensors (and other sources) from 3rd parties may include their time reference in some 
proprietary format. In this case a suitable decoder from `acp_decoders` may create the `acp_ts`
property from the encoding of time in the data.

In the absence of any recognized time value in the sensor data, the `acp_decoders` 
`DecoderManager` will create `acp_ts` with the current system timestamp.

## Space

Global position information for the sensor data is standardized as:

* `acp_lat`: floating point WGS84 latitude (North positive)
* `acp_lng`: floating point WGS84 longitude (East positive)
* `acp_alt`: floating point WGS84 altitude in meters.

For mobile sensors, location information is likely to included in the sensor data and this may be
interpreted by `acp_decoders` such that these properties can be populated (if the sensor has not
already).

Alternatively, the location information for a sensor may be provided by the sensor metadata database (see
below), via an API lookup using the sensor identifier.

In-building position information may use an alternate coordinate system (for example as x,y coordinates in meters plus
a floor number). This information will be supported in the Platform via a `acp_location` property e.g.:

```
"acp_location": { "system": "WGB", "x": "2131.33", "y": "53272.22", "z": "1"} 
```
In this case, the `system` property of the `acp_location` JSON object determines the expected other properties
representing the location.

The sensor metadata database will include information enabling the `acp_location/system` to be translated to
`acp_lat`, `acp_lng` and `acp_alt`.

## Sensor metadata database

Name: postgres

## Tables
### metadata
This table stores the metadata information of all the sensors being deployed. It has two columns as of now;
+ acp_id (VARCHAR): This is the unique id given to each of the deployed sennsors.
+ info (jsonb): This currently stores all the information of the sensor. As different category of sensors could have specific metadata information unique to itself, we opted for a jsonb type.

Example Rows:

|      acp_id      |                                                                  info                                                                 |
| ---------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| avatar-test-001  | {"ts":"1585138617","type":"smartplug","owner":"rv355","source":"mqtt_csn","features":["power"],"acp_location":{"x":"2131.33","y":"53272.22","z":"1","system":"WGB"}} |
| aoycocr-test-001 | {"ts":"1585138617","type":"smartplug","owner":"jb2328","source":"mqtt_csn","features":["power"],"acp_location":{"x":"2654.33","y":"53432.22","z":"1","system":"WGB"}} |
| gosund-test-001  | {"ts":"1585138617","type":"smartplug","owner":"mrd45","source":"mqtt_csn","features":["power"],"acp_location":{"x":"2664.33","y":"53432.22","z":"1","system":"WGB"}} |
| ijl20-sodaq-ttn  | {"ts": "1585868424", "type": "temperature", "owner": "ijl20", "source": "mqtt_ttn", "features": ["temperature"], "acp_location": {"system": "GPS", "acp_alt": "15", "acp_lat": "52.21124", "acp_lng": "0.09383"}} |

In the above example the info field includes;
+ acp_ts: The Unix timestamp when the metadata was stored. Owing to the fact that the location could change later we have opted to include timestamp.
+ type: type of sensor
+ owner: the owner of the device
+ source: the mqtt source which is publishing the messages from the sensor
+ features: set of features of which the sensor logs information of
+ acp_location: The location of the sensor. This could be either inside a building in which case we use building specific system like WGB and (x,y,z). This system could be mapped to a latitude, longitude and altitude system and vice-versa.