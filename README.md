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
