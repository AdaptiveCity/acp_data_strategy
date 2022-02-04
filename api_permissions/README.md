# Permissions API

This is the API to check access control rights for anyone trying to access the platform.

## /get_permission/<person_id>/<object_id>/<object_type>/<operation_type>

Checks if a person `person_id` has access to perform an operation `operation_type` on a resource `object_id` of type `object_type`.

E.g.
```
http://ijl20-iot/api/permission/get_permission/rv355/elsys-co2-041ba9/sensor/write
```
The above call traverses through all permission checks available in the file `permission_rules.json` (will be later stored in db) to check if `rv355` has write access to the `sensor` with id `elsys-co2-041ba9`.

## The Permission Object
A permission object in the `permission_rules.json` file contains the `subject`, `resource`, `action`, `options`, and `decision_point`.
+ `subject`: The object that requests for a permssion.
+ `resource`: The object for which permission is requested.
+ `action`: The type of permission requested.
+ `options`: Any additional attributes that impact the permission. For example, time or date when the permission is being requested. Or if the permission should search recurrsively.
+ `decision_point`: The function that will be used to provide the permission.

```
{
    "admin_access" : {
        "permission_id": "admin_access",
        "permission_info": {
            "subject" : {
                "subject_type": "people",
                "subject_id": "person_id",
                "subject_api": "PEOPLE",
                "value": "999999"
            },
            "resource": {
                "resource_type": "people",
                "resource_id": "group_id",
                "resource_api": "PEOPLE",
                "value": "groups.group_id"
            },
            "action": ["C", "R", "U", "D"],
            "options": "",
            "decision_point": "resource_check"
        }
    },

    "delete_sensor_access" : {
        "permission_id": "delete_sensor_access",
        "permission_info": {
            "subject" : {
                "subject_type": "people",
                "subject_id": "person_id",
                "subject_api": "PEOPLE",
                "value": "999999"
            },
            "resource": {
                "resource_type": "people",
                "resource_id": "group_id",
                "resource_api": "PEOPLE",
                "value": "groups.group_id"
            },
            "action": ["D"],
            "options": {
                "time_check": {
                    "day": ["Saturday", "Sunday", "Friday"],
                    "time": "20:00:00",
                    "time_condition": "pre"
                }
            },
            "decision_point": "resource_check"
        }
    },

    "occupies_read_access" : {
        "permission_id": "occupies_read_access",
        "permission_info": {
            "subject" : {
                "subject_type": "people",
                "subject_id": "person_id",
                "subject_api": "PEOPLE",
                "value": "bim.crate_id"
            },
            "resource": {
                "resource_type": "sensors",
                "resource_id": "sensor_id",
                "resource_api": "SENSORS",
                "value": "crate_id"
            },
            "action": ["R"],
            "options": {
                "recurrsive": {
                    "recurrsive": "True",
                    "subject" : {},
                    "resource": {
                        "resource_type": "bim",
                        "resource_id": "crate_id",
                        "resource_api": "BIM",
                        "value": "parent_crate_path"
                    }
                }
            },
            "decision_point": "subject_resource_compare"
        }
    }
}
```

## Additional Setting

A `permission_order` setting should be added to the `settings.json` file to define the precendence of permissions to be checked. For example, it is better to check for admin access for a user, which if available implies all other permissions are available.
```
"permission_order": ["admin_access", delete_sensor_access, "occupies_read_access"]
```
**Note:** Might not be required.