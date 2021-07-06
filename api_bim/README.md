# BIM API

This is the API to access metadata for building objects, such as their type, shape and location. In our system BIM objects
are distinguished by having a hierarchical relevance, i.e. an object 'First Floor' might be considered the 'parent' of
'Office FE11'. In terms of the underlying implementation this linkage is best thought of as more generally *relational* (i.e. the
relation 'parent' is true for objects 'First Floor' and 'Office FE11').

This data is stored as JSON objects in a *timestamped transaction log object store*, i.e. when objects are updated a new record
is created, with the previous record timestamped as no longer current.

Information returned for a BIM object (e.g. via `/get/`) is a JSON object as stored (and displayed on `acp_web`).

## /get/<crate_id>/[<depth>/]?path=

Gets the BIM data for the selected crate, plus its children to selected depth. If `path` is true, then another key `parent_crate_path` is included in the `crate_info`, which includes all the parent crates up the crate hierarchy.

E.g.
```
http://ijl20-iot/api/bim/get/FF/1/?path=true
```
gets all the BIM objects that have `"parent_crate_id": "FF"`.

Results are returned as a dictionary keyed on `crate_id`.

## /get_floor_number/<coordinate_system>/<floor_number>/

Returns BIM objects for floor EXCLUDING crate_type=="floor"

Results are returned as a dictionary keyed on `crate_id`.

## /get_gps/<crate_id>/[<depth>/]

Similar to `/get/` but will include `acp_boundary_gps` using lat/lng coordinates (so can render on map).

Note this `acp_boundary_gps` property will be added the cached object entry for the selected object(s).

## /get_xyzf/<crate_id>/[<depth>/]

Similar to `/get/` but will include `acp_boundary_xyz` using rectilinear x/y coordinates in meters.

Note this `acp_boundary_xyz` property will be added the cached object entry for the selected object(s).
