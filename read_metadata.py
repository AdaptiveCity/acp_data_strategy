from CONFIG import *
from dbconn import *
import json
from math import inf

# Returns all the data sources available for ACP
def getSources():

    query = "SELECT distinct sensor_info->'source' from "+TABLE_MD
    sourcelist = []

    rows = dbread(query)
    for row in rows:
        sourcelist.append(row[0])

    return sourcelist

# Returns all sensor names (acp_id) corresponding to a data source. 
# If no source is specified then all sensors are returned.
def getSensors(source):

    query = ''
    sensorlist = []

    if source == "":
        query = "SELECT acp_id from "+TABLE_MD
    else:
        query = "SELECT acp_id from "+TABLE_MD+ " WHERE sensor_info->>'source'='"+source+"'"

    rows = dbread(query)
    for row in rows:
        sensorlist.append(row[0])
    return sensorlist

# Returns all the data attributes the given sensor supports.
def getFeatures(sensor):
    query = "SELECT sensor_info->'features' from "+TABLE_MD+ " WHERE acp_id='"+sensor+"'"

    rows = dbread(query)
    return rows[0][0].split(',')

# Recurrsively finds all the rooms in a given crate.
def getRoomsInCrate(crate_id):
    query = "SELECT * from "+TABLE_BIM+" WHERE bim_info->>'parent_crate_id'='"+crate_id+"'"
    roomList = []
    
    rows = dbread(query)
    for row in rows:
        if row[1]['crate_type'] == 'room':            
            roomList.append(row[0])
        else:
            roomList.extend(getRoomsInCrate(row[0]))
    return roomList

# Finds all the sensors in a crate and its child crates
def getSensorsInCrate(crate_id):
    roomList = getRoomsInCrate(crate_id)
    sensorList = []

    if len(roomList) == 0:
        listString = "'"+crate_id+"'"
    else:
        listString = ""

        for r in roomList:
            listString = listString+"'"+r+"',"
        listString = listString[:-1]

    query = "SELECT acp_id from "+TABLE_MD+" WHERE sensor_info->>'parent_crate_id' in ("+listString+")"

    rows = dbread(query)

    for row in rows:
        sensorList.append(row[0])

    return sensorList

# Returns the child crates upto level 'children' of a given crate
def getChildCrates(crate_id, children=inf):
    if children == 0:
        return []
    query = "SELECT * from "+TABLE_BIM+" WHERE bim_info->>'parent_crate_id'='"+crate_id+"'"
    roomList = []
    
    rows = dbread(query)
    for row in rows:
        roomList.append(row[0])
        if row[1]['crate_type'] != 'room':
            roomList.extend(getChildCrates(row[0], children-1))
    return roomList

# Returns all info available for a crate and of its children crates upto
# level 'children'.
def getCrateDetails(crate_id, children=inf):
    cList = [crate_id]
    rsList = []

    cList.extend(getChildCrates(crate_id, children))
    listStr = ""

    for r in cList:
        listStr = listStr+"'"+r+"',"
    listStr = listStr[:-1]

    query = "SELECT * from "+TABLE_BIM+" WHERE crate_id in ("+listStr+")"
    rows = dbread(query)
    for row in rows:
        row[1]['crate_id']=row[0]
        rsList.append(row[1])
    return rsList

# Returns all the crates on a floor in a given system
def getCratesOnFloor(system, floor_number):
    crateList = []

    query = "SELECT crate_id FROM "+TABLE_BIM+" WHERE bim_info->'acp_location'->'f' = '"+str(floor_number)+"' and  bim_info->'acp_location'->'system' = '\""+system+"\"'"

    print(query)
    rows = dbread(query)
    for row in rows:
        crateList.append(row[0])
    return crateList
    
# Returns details of a given sensor
def getSensorDetails(acp_id):
    query = "SELECT * FROM "+TABLE_MD+" WHERE acp_id = '"+acp_id+"'"
    rows = dbread(query)

    rows[0][1]['acp_id']=rows[0][0]

    return rows[0][1]

# Returns the total number of sensors inside a list of crates
def getSensorCount(response):
    crateList = []
    for r in response['data']:
        crateList.append(r['crate']['crate_id'])

    listString = ''
    for c in crateList:
        listString = listString+"'"+c+"',"
    listString = listString[:-1]
    
    query = "SELECT acp_id from "+TABLE_MD+" WHERE sensor_info->>'parent_crate_id' in ("+listString+")"
    
    rows = dbread(query)

    return len(rows)
