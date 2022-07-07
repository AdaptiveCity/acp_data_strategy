# Display API

This is the API to access metadata for display objects, such as the device pin and portal pages to be displayed. 

This data is stored as JSON objects in a *timestamped transaction log object store*, i.e. when objects are updated a new record
is created, with the previous record timestamped as no longer current.

Information returned for a Displays object (e.g. via `/get/`) is a JSON object as stored (and displayed on `acp_web`).

## /get/<display_id>/

Gets the display data for the selected display_id.

E.g.
```
http://ijl20-iot/api/displays/get/display-tab-12345/
```
gets the Display object that has `"display_id": "display-tab-12345"`.

