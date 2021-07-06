# People API

This is the API to access metadata for people objects, such as their name, groups and institutions. In our system institutions
are distinguished by having a hierarchical relevance, i.e. an institutions 'CL' is considered the 'parent' of
'ACSMP18' and 'child' of 'IUSCTEC'. This essentially means that a person who is a member of 'CL' would also be a member of the child institutions.

This data is stored as JSON objects in a *timestamped transaction log object store*, i.e. when objects are updated a new record
is created, with the previous record timestamped as no longer current.

Information returned for a People object (e.g. via `/get/`) is a JSON object as stored (and displayed on `acp_web`).

## /get/<person_id>/?path=

Gets the person data for the selected person_id, plus its parents and child institutions.
`path = true` searches for all institutions up the institution hierarchy to which person_id belongs to.

E.g.
```
http://ijl20-iot/api/people/get/crsid-rv355/?path=true
```
gets the People object that has `"person_id": "crsid-rv355"`. In addition to the listed institutions for 'person_id' all its parent institutions up the institution hierarchy are also listed.

