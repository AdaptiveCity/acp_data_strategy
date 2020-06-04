from CONFIG import *
from dbconn import *
import sys
from datetime import datetime
import json

DEBUG = True

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

def validateNewElement(new_elements):
    
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
            return False
    return True, newElementDict


def updateMetadata(acp_id, stype, source, owner, features, acp_location, new_elements):
    acplocValidation = validateLocationInput(acp_location)
    newElementValidation, newElementDict = validateNewElement(new_elements)
    print(acplocValidation,newElementValidation,newElementDict)
    if not acplocValidation or not newElementValidation:
        return False
    
    ts = datetime.timestamp(datetime.now())
    data = {"ts":ts,"type":stype, "source":source, "owner":owner, "features":features, "acp_location":json.loads(acp_location)}
    data.update(newElementDict)

    flag = False

    query = "INSERT INTO " + TABLE_MD + " (acp_id, sensor_info) VALUES ('" + acp_id + "','" + json.dumps(data) + "')"
    try:
        dbwrite(query)
        flag = True
    except:
        if DEBUG:
            print(sys.exc_info())
    
    return flag