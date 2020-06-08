from CONFIG import *
from dbconn import *
import sys
from datetime import datetime
import json

DEBUG = True

# Validate that the user entered location input is valid
def validateLocationInput(acp_location):
    validation = False
    try:
        jData = json.loads(acp_location)
        if jData['system'] == 'GPS':
            if isinstance(jData['acp_lat'], (float, int)) and isinstance(jData['acp_lng'], (float, int)) and isinstance(jData['acp_alt'], (float, int)):
                validation = True
        elif jData['system'] == 'WGB':
            if isinstance(jData['x'], (float, int)) and isinstance(jData['y'], (float, int)) and isinstance(jData['f'], (float, int)) and isinstance(jData['zf'], (float, int)):
                validation = True
        elif jData['system'] == "OLH":
            if 'crate_id' in jData and 'parent_crate_id' in jData and 'crate_type' in jData:
                validation = True
    except:
        if DEBUG:
            print(sys.exc_info())

    return validation

# Validate that the user entered new elements input is in valid format
# and return the dictionary of (key,value) pairs
def validateNewElement(new_elements):
    
    if len(new_elements) < 2:
        return True, None

    elementData = new_elements.split(';')
    
    newElementDict = {}
    for element in elementData:
        try:
            eData = element.split(':')
            # print(eData)
            newElementDict.update({eData[0]:eData[1]})
        except:
            if DEBUG:
                print(sys.exc_info())
            return False, None
    return True, newElementDict

# Validate if the boundary provided by the user is valid.
def validateBoundary(acp_boundary):
    boundaryList = acp_boundary.strip().split(',')
    if len(boundaryList)%2 == 0:
        return True
    else:
        return False

# Validate if the parent crate already exists in the database.
def validateParent(parent_crate_id):
    query = "SELECT count(*) FROM "+TABLE_BIM+" WHERE crate_id='"+parent_crate_id+"'"

    rows = dbread(query)
    if rows[0][0] > 0:
        return True
    return False

# Add/Update sensor information based on user input after validation
def updateSensorMetadata(acp_id, stype, source, owner, features, acp_location, new_elements):
    acplocValidation = validateLocationInput(acp_location)
    
    if not acplocValidation:
        return False
    
    ts = datetime.timestamp(datetime.now())
    acpdata = {"acp_ts":ts,"type":stype, "source":source, "owner":owner, "features":features, "acp_location":json.loads(acp_location)}
    
    newElementValidation, newElementDict = validateNewElement(new_elements)
    if not newElementValidation:
        return False
    if newElementDict != None:
        acpdata.update(newElementDict)

    flag = False

    query = "INSERT INTO " + TABLE_MD + " (acp_id, sensor_info) VALUES ('" + acp_id + "','" + json.dumps(acpdata) + "')"
    try:
        dbwrite(query)
        flag = True
    except:
        if DEBUG:
            print(sys.exc_info())
    
    return flag

# Add/Update bim information based on user input after validation
def updateBimMetadata(crate_id, parent_crate_id, long_name, ctype, description, acp_boundary, acp_location, new_elements):
    acplocValidation = validateLocationInput(acp_location)
    acpboundaryValidation = validateBoundary(acp_boundary)
    parentValidation = validateParent(parent_crate_id)

    if not acplocValidation or not acpboundaryValidation or not parentValidation:
        return False
    
    ts = datetime.timestamp(datetime.now())
    acp_boundary = "{"+acp_boundary+"}"
    bimdata = {"acp_ts": ts,"long-name": long_name,"crate_type": ctype,"description": description,"acp_boundary": acp_boundary,"parent_crate_id": parent_crate_id,"acp_location":json.loads(acp_location)}

    newElementValidation, newElementDict = validateNewElement(new_elements)
    if not newElementValidation:
        return False
    if newElementDict != None:
        bimdata.update(newElementDict)

    flag = False

    query = "INSERT INTO " + TABLE_BIM + " (crate_id, bim_info) VALUES ('" + crate_id + "','" + json.dumps(bimdata) + "')"
    try:
        dbwrite(query)
        flag = True
    except:
        if DEBUG:
            print(sys.exc_info())
    
    return flag