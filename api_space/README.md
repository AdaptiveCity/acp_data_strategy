# Space API

The Space API returns rendering information for ACP objects, typically as SVG. Web pages that render buildings, floors etc will
receive data from the Space API.

The SVG coordinates are consistently in meters, aligned to the in-building coordinate system for the object concerned.

The initial implementation of the Space API returned SVG directly (i.e. `text/xml`). This has been extended with
equivalent methods that return JSON (i.e. `application/json`) for consistency with the other ACP API's. Within the
JSON returned, the SVG content is base64 encoded in a property `svg_encoded`.


## `/get_bim_json/<crate_id>/[<children=0>/]`

Returns JSON with the SVG for the requested objects base64 encoded in property `svg_encoded`.
In the future the JSON may have additional properties.

The SVG is for the selected bim object and its children. Optional parameter gives depth to retrieve children, defaulting
to `0`.

Outermost SVG element is `<svg>`

This `<svg>` element will contain a sequence of `<g class="crate">` elements representing each of the BIM objects
requested.

## `/get_bim/<crate_id>/[<children=0>/]`

This API call is deprecated. See `/get_bim_json/...` above.

## `/get_floor_number_json/<coordinate_system>/<floor_number>/`

Returning a similar JSON/SVG object to `/get_bim_json/` above, this API call selected the BIM objects using the floor
identifier (an integer) within the coordinate system, rather than using a `crate_id`.

## `/get_floor_number/<coordinate_system>/<floor_number>/`

This API call is deprecated. See `/get_floor_number_json/...` above.
