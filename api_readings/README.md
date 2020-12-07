# Readings API - sensor readings

## /get/<acp_id>/?<args>

The canonical "get" API call: /get/<acp_id>/[?metadata=true]

Returns :
```
{ "reading": <the latest sensor reading>,
  "sensor_metadata": <sensors API data for this sensor> (optional)
}
```
where:

`<acp_id>` is the sensor identifier

`?metadata=true` requests the sensor metadata to be included in the response

Note that this call always returns the contents of the most recent sensor message (i.e. its reading). Some
sensors send different messages at different times, e.g. a `co2` reading might be sent periodically but the
same sensor might send a `motion` message asynchronously separate from the `co2` readings. In all cases
this `/get/` API call will return the most recent message and in the example given this may or may not contain
a `co2` feature value. If required, the `/get_feature/` API call is provided to return the most recent reading containing a
given feature.

## /get_day/<acp_id>/[?date=YYYY-MM-DD][&metadata=true]

Returns a day's-worth of readings for the required sensor.

Defaults to 'today', or optional date can be given.

Sensor metadata can also be returned as for /get/.

## /get_feature/<acp_id>/<feature_id>/[?metadata=true]

Similar to `/get/` except the API call will search backwards through messages to find most recent that contains a value
for `<feature_id>`. The search is limited to until start-of-day i.e. 00:00:00.

E.g. `/get_feature/elsys-eye-044504/temperature/?metadata=true`
