# Adaptive City Program sensor data strategy

This repo is intended to pull together the multiple approaches we're taking to normalize
the data coming in from our various sensors and sources.  This does *not* mean we assume
some miraculous uber-standard will magically make all the data sources adhere to common
protocols and formats. Rather, we are assuming the data will continue to be tailored to
each source and consequently be fairly diverse and we will take steps *where appropriate*
to make the data manageable.

For the API details, see the README.md for each API family, i.e.
* [BIM API](api_bim/README.md)
* [Readings API](api_readings/README.md)
* [Sensors API](api_sensors/README.md)
* [People API](api_people/README.md)
* [Space API](api_space/README.md)
* [Permission API](api_permissions/README.md)
* [Displays API](api_display/README.md)

## Installation

See [INSTALLATION.md](INSTALLATION.md).

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

5. Reference data (i.e. everything except readings) are stored using a *timestamped transaction log*
approach. I.e. an 'update' to the data results in a new timestamped data record, and the previous record
is retained but flagged as being no longer current.

There are two significant platform elements relevant to our approach:

1. `acp_decoders`: a real-time component part of the
[acp_local_mqtt](https://github.com/AdaptiveCity/acp_local_mqtt) project, which subscribes to
incoming data and allows the dynamic addition of *decoders* capable of extracting and normalizing
key properties such that the annotated data can be re-published for consumption further
downstream like any other real-time data source.

2. The `metadata database` (documented below) which acts as a repository for
persistent metadata regarding the sensors which is accessible via an API for any process
during the data flow. For example this includes the `location` of the non-moving sensors.

## Storage method

Recognizing the 'data' is generally stored as JSON objects, we use PostgreSQL as a 'transaction log object store'. This
supports two key requirements:

* The 'get' method `object_id` -> `json object`

* The use of timestamps such that *updated* objects are stored as *new* object values, with the previous value retained but
given an 'end date'.

Consequently our generalized PostgreSQL table structure is:

`record_id`, `<object_id>`, `acp_ts`, `acp_ts_end`, `<object_json>`

where the names for `<object_id>` and `<object_json>` will be determined by the object type stored (e.g. for the
table `sensors`, the `<object_id>` is `acp_id`, and the `<object_json>` is `sensor_info`.

`record_id` is a unique value for this particular 'row' in the table, used to facilitate data management e.g. the hard delete
of a broken entry.

`<object_id>` is the name of the identifier for the current object type (e.g. `acp_id`, `acp_type_id`, `crate_id`).

`<acp_ts>` is the timestamp this particular record for the object was created.

`acp_ts_end` is the timestamp when this record was superceded by a more recent entry. By definition, this `acp_ts_end` will be
the `acp_ts` value from the new entry. `acp_ts_end` will be `NULL` for the latest entry.

`<object_json>` e.g. (`sensor_info`, `type_info`, `crate_info`) is the JSON data to be returned in a `/get/<object_id>/` API call.

## Standard data fields in the JSON objects

### Summary

`acp_id`: sensor identifier, globally unique e.g. `elsys-eye-049876`.

`acp_type_id`: object (e.g. sensor) type, determines data format e.g. `elsys-eye`.

`acp_event`: event type, for timestamped events, e.g. `openclose`.

`acp_event_value`: qualifier or data reading for event, e.g. `open`.

`acp_ts`: epoch timestamp seconds most relevant to data reading or event, e.g. `"1586461606.465372"` (the decimal part is optional).

`acp_ts_end`: if the data reading represents a period, epoch timestamp most relevant to the 'end' of the
data reading or event, e.g. `"1586461609.5372"`.

`acp_location`: location using a coordinate system e.g. `{ "system": "WGB", "x": 12, "y":45, "f": 1 }`. The WGS84
coordinate system is predefined with `{ "system": "GPS", "lat": 52.123456, "lng": 0.123, "alt": 42 }` where
altitude (meters) is optional. All other coordinate systems are `
{ "system": "<system_id>", ... <any other parameters relevant to that system }`

`acp_confidence`: a value `0..1` indicating the reliability of the sensor reading.

An important distinction of our approach is to concentrate on fields essential to our architectural approach (like
locations and timestamps) and *not* confuse that with a construction ontology such as the meaning of 'concrete' or 'window'.

### Identity

`acp_id` is our globally-recognized string containing a sensor identifier. In many cases our
feedhandlers or MQTT decoders will extract the relevant string from a custom data format and
use this to populate `acp_id`. A simple agreed property name for the sensor identifier means
much of our system can proceed independent of the sensor type, e.g. selecting messages from
a particular sensor. It is (strangely) common for retail sensors sending readings via MQTT to
*not* include their sensor identity in the data message, rather embedding it somewhere within
a proprietary MQTT topic format. In this case the ACP decoders will typically extract the sensor
id from the topic and add a `acp_id` value to the data message.

`acp_type_id` is the common string property which hints at the sensor type, e.g. `elsys-co2`. If
included in the raw incoming data (i.e. from our own sensors) this allows rapid selection of
appropriate stream processing, rather then a complex heuristic based on the message content
or format. If missing from the original data, we aim to attach this property as early as
practicable in the stream processing.

### Events

Incoming sensor data messages to the platform can be broadly categorized as *periodic* or
*event* based. The Adaptive City platform is designed throughout to handle events in a
timely manner, and includes pre-defined data fields to make event-based messages easy to
recognize. Any event on the platform is represented as the following JSON dictionary;

```
acp_event : {
    acp_event_type : {
        "acp_event_type" : <a globally-recognized string defining the event *type*. Must be the same as the key acp_event_type>,
        "acp_event_value": is the event property specific to the event
    }
}
```
Some examples of the "acp_event":
```
{
    ....
    ....
    "acp_event" : {
        "openclose" : {
            "acp_event_type": "openclose",
            "acp_event_value": "open"
        }
    }
    ....
    ....

}
```

```
{
    ....
    ....
    "acp_event": {
        "up": {
            "acp_event_type": "up",
            "acp_event_value": []
        },
        "down": {
            "acp_event_type": "down",
            "acp_event_value": [
                "csn-mtcdtip-005f06"
            ]
        },
        "new": {
            "acp_event_type": "new",
            "acp_event_value": []
        }
    },
    ....
    ....
}
```

Note that these common properties are *in addition* to the data that the sensor will include
in its message anyway (Denoted by `....` in the examples above). They are a convenience such that the recognition of significant
events can be less complex for downstream processing which is likely to ignore or analyze the
message in more detail.

### Time

Sensors often take a certain amount of time to gather data necessary to produce a reading (like ingesting
sufficient air to accurately measure CO2 or particulates), perhaps in this case the 'best' time to associate
with the sensor reading is when that process completes. A neural network may take a snapshot of a scene and then
take some time analyzing the image to produce an object count - in this example the timestamp when the image was
taken is likely to be the most appropriate to associate with the 'readings'. These times may differ from the time
the sensor transmits the data (or the data is polled-for and read by a server). Consequently we
consider the idea of *the* time for an event as somewhat simplistic, but we want as much consistency as
possible in dealing with time in our system. Hence we define a generalized time property (`acp_ts`) as whatever
the data owner considers the most appropriate time for a given event (i.e. sensor reading or update to metadata). In
addition other timestamps can be included (e.g. we *always* timestamp the data when it arrives on our platform) but they
should not be confused with `acp_ts`.

`acp_ts` is intended for the property containing the timestamp most relevant to the sensor
data reading, containing the floating point seconds in epoch stored in a STRING (this is to remove
dependency on multi-system floating point precision).

For example UTC date/time 2020-04-09 19:46:46 and 465372 microseconds is:
```
"acp_ts": "1586461606.465372"
```

`acp_ts_end` is a similar value, representing the end of a time period. In particular this is used
when a metadata value (such as sensor properties) is updated. A new JSON object will be created with
the current time as `acp_ts`, and the previous object will be given an `acp_ts_end` property  with the same value.

Sensors designed within the project will include `acp_ts` in their transmitted data as the
definitive time of the sensor reading, along with other timestamps from the internal processes of
the sensor.

Sensors (and other sources) from 3rd parties may include their time reference in some
proprietary format. In this case a suitable decoder from `acp_decoders` may create the `acp_ts`
property from the encoding of time in the data.

In the absence of any recognized time value in the sensor data, the `acp_decoders`
`DecoderManager` will create `acp_ts` with the current system timestamp.

### Spatial coordinates

We require consistent support for **three**  parellel location reference systems:

1. **Global:** The only definitive common reference system constituting of latitude, longitude and altitude. Necessary for outdoor sensors and
the coordinate system used while interacting with 'map' views of sensors or data.

2. **In-building coordinates:** This will be a spatial coordinate system typically unique to a given building, typically
used when interacting with in-building floorplan or 3D views of sensors or data. Sensors that transmit their position in the
building (i.e. particularly sensors that move around) may use this system in their sensor data.

3. **Building object hierarchy:** Often used in Building Information Models. It reasonable for a sensor (or monitored device)
to be recorded as being in location `FE11` i.e. a room/office which relates to BIM data structured as `site`..`building`..`floor`..
`room`..`window`. This hierarchy is often natively used when collating or browsing in-building information (e.g. the electricity
use in lecture theaters, William Gates Building).

Effective support implies a set of **API's** which support:

1. Translation between these location reference systems. This does not necessarily need to be perfectly granular, e.g. for
some purposes a mapping of all in-building coordinates to a single lat/lng/alt will allow macro processing at a map level including
outdoor and in-building sensors.

2. Rapid access to current and historical locations of assets (i.e. sensors and other objects of interest). It should be
feasible that a lookup of the data occurs at the rate of the incoming sensor data.

3. An ability to update the sensor and asset metadata (such as location) such that 'downstream' processing recognizes the
change with appropriate timeliness either by referring to the definitive metadata source on the arrival of each sensor data message
or by providing a 'push' mechanism when the metadata changes.

#### Global

Global position information for the sensor data is standardized as:
```
"acp_location": { "system": "GPS", "lat": 52.1234, "lng": 0.1234567, "alt": 42 }
```
where
* `lat`: floating point WGS84 latitude (North positive)
* `lng`: floating point WGS84 longitude (East positive)
* `alt`: optional floating point WGS84 altitude in meters.

For mobile sensors, location information is likely to included in the sensor data and this may be
interpreted by `acp_decoders` such that these properties can be populated (if the sensor has not
already).

Alternatively, the location information for a sensor may be provided by the sensor metadata database (see
below), via an API lookup using the sensor identifier.

#### In-building coordinates

In-building position information may use an alternate coordinate system (for example as x,y coordinates in meters plus
a floor number and height from the floor reference as z). This information will be supported in the Platform via a `acp_location` property for example (this is not
a genuine system in use):

```
"acp_location": { "system": "WGB", "x": "20.33", "y": "53.22", "f": "1", "zf":"0.5"}
```
In this case, the `system` property of the `acp_location` JSON object determines the expected other properties
representing the location, in this case `x,y,f,zf` where `x` and `y` are in meters relative to some arbitrary `0,0`
and orientation, a `f` is a floor number, and `zf` is the height of the sensor calculated with the floor as reference. Below we show an example of such a system for the William Gates Building (WGB).

![2D](static/images/2d.png)

Considering the above figure as a reference, with the origin at the lower left corner, any point in the building could be assigned an `x` and `y` value corresponding to its distance from the axis. For eg., the point P1 in the Lecture Theatre 1 would have its `x,y` set as `35.4,5.6`.

![3D](static/images/3d.png)

The figure above shows how the z-axis would be recorded as a combination of floor number and relative height from the floor reference. Both sensor S1 and S2 are `0.5 m` above the floor reference, so would get the coordinate assigned as `(5.3 3.2, 0, 0.5)` and `(72.7, 38.1, 1, 0.5)
` respectively.

The sensor metadata database will include information enabling the `acp_location/system` to be translated to
`acp_lat`, `acp_lng` and `acp_alt`.

#### Object-level hierarchy

We will use the data currently contained in the IfM BIM (Building Information Model) as a typical example of extant
metadata relating to in-building assets and sensors.

The objective is to support navigating the hierarchical model *including* real-time and historical information available
from sensors, including sensors that may continually change information the BIM assumes is static (for example
a robot leaner that moves around).

The BIM system itself is likely to fall short of our requirements for rapid programmatic access to the reference data
or the ability to update the information promptly and communicate those changes, nevertheless a system design approach is
required that assumes some substantive building reference information remains embedded in an 'external' system.

In the BIM system, we consider each object is treated as a crate owing to the analogy of hierarchy with each smaller crate put into a bigger one. For eg, WGB would be a crate with the floors being smaller crates put into the WGB crate. The rooms on each floor would be separate crates put into crates corresponding to the floor crates. An example representation is shown below;

| crate_id 	| parent_crate_id 	|                                  location                                 	|                        boundary                        	| crate_type 	|
|:--------:	|:---------------:	|:-------------------------------------------------------------------------:	|:------------------------------------------------------:	|:----------:	|
|    WGB   	|        -        	| {"system":"GPS", "acp_lat":52.2108765, "acp_lng":0.0912775, "acp_alt":0.0} 	|         {"system":"WGB",[0,0,0,78,73,78,73,0]}         	| "building" 	|
|    GF    	|       WGB       	|             {"system":"WGB", "x":36.5, "y":39, "f":0, "zf":0}             	|         {"system":"WGB",[0,0,0,78,73,78,73,0]}         	|   "floor"  	|
|   GN15   	|        GF       	|              {"system":"WGB", "x":38, "y":70, "f":0, "zf":0}              	| {"system":"WGB",[35,68,35,73,40,73,40,73,38,70,38,68]} 	|   "room"   	|

In the above example, each column is defined as follows;

`crate_id` - An identifier for the particular object.\
`parent_crate_id` - The crate which holds the object with the given crate_id. Assuming a building as the outermost crate, WGB has no parent.\
`location` - A unique location identifier for the object. When inside a building, the location would the corresponding In-building system.\
`boundary` - This field stores the coordinates of the vertices of the polygon forming the object. Any object would be mapped to a polygon having each vertex corresponding to an In-building coordinate. The standard being to start from the vertex on the leftmost lower corner of the object and then moving counter-clockwise. \
`crate_type` - The type of that particular object.

#### Coordinate Translation

##### In-building <-> Global

![CtoG](static/images/ctog.png)

As shown in the above figure, the translation uses the Global coordinates at the three corners of the building for translation. The (`lat`,`lng`) at the origin of the In-building coordinate system is taken as (`lat_origin`, `lng_origin`). A pair of global coordinates (`lat1`, `lng1`) and (`lat2`, `lng2`) are selected such that an inverse L could be formed.

For the translation on the XY-plane, we would be requiring vertical and horizontal shifts which could be calculated as;

<blockquote>
vertical shift (vs) = &Delta;y/&Delta;lat

horizontal shift (hs) = &Delta;x/(cos(lat)*&Delta;lng)
</blockquote>

###### Global -> In-building
Thus, given global coordinates (lat, lng) the translation to In-building coordinates (x,y) would be calculated as;

<blockquote>
x = (lng - lng_origin)*hs

y = (lat - lat_origin)*vs
</blockquote>

###### In-building -> Global
Alternatively, given (x,y), the translation to (lat, lng) would be calculated as;

<blockquote>
lat = lat_origin + (y*&Delta;lat)/&Delta;y

lng = lng_origin + (x*cos(lat)*&Delta;lng)/&Delta;x
</blockquote>

###### Translation along z-axis

Each floor number would be assigned a height in meters with respect to the system being followed and stored in a table. So the translation along the z-axis would be;

<blockquote>
alt = floor height + zf
</blockquote>

It should be noted that for a different building, the values of (lat_origin, lng_origin, &Delta;lat, &Delta;lng, &Delta;x, &Delta;y) would change.

##### In-building <-> Object-level

This translation would utilize a mapping between the two systems described by the `boundary` field in the BIM. Any object in the Object-level system would mapped to a polygon having each vertex corresponding to an In-building coordinate.

With the available mapping, any point in the In-building system could be mapped to being in any one of these polygons and consequently to the corresponding room in the Object-level system.

An example is given in figure below. The room `GN17` in the Object-level system would be mapped to the coordinates belonging to the polygon `ABCDEF`. Conversely, any point inside this polygon would be mapped to `GN17`.

![ol](static/images/ol.png)

### Confidence

`acp_confidence` indicates a general probability a data reading is reliable, on a scale `0..1`. This property is
useful as a common generalization. For example, a sensor that is deriving traffic speed from passing vehicles
will assign more confidence to a value based on many vehicles than on a few. *How* the confidence value is
calculated will differ by sensor type and it is currently not clear how this should best be normalized.

The essential point is that confidence in a sensor reading is a general issue, not particularly limited to a few
sensor types, so it is helpful on the Adaptive City platform to abstract this into a common property. Note this is, as with
the other standardized fields, *in addition* to the data values the sensor will send anyway allowing downstream processing
knowledgeable about the intricacies of the particular sensor to make its own interpretation of confidence or accuracy.

## API References

Four classes of API are available:

#### BIM API

Returns data on BIM objects e.g. an office.

See [BIM API README.md](api_bim/README.md)

#### Readings API

Returns sensors readings data.

See [Readings API README.md](api_readings/README.md)

#### Sensors APIs

Returns metadata regarding sensors, e.g. the location.

Also returns sensor *type* information, e.g. the properties of a `monnit-Temperature` sensor type.

See [Sensors API README.md](ap_sensors/README.md).

#### Space API

Returns SVG drawing information for BIM objects.

See [Space API README.md](api_space/README.md).
