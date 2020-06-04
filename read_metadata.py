from CONFIG import *
from dbconn import *
import json
from math import inf

def getSources():

    query = "SELECT distinct sensor_info->'source' from "+TABLE_MD
    slist = []

    rows = dbread(query)
    for row in rows:
        slist.append(row[0])

    return slist

def getSensors(source):

    query = ''
    slist = []

    if source == "":
        query = "SELECT acp_id from "+TABLE_MD
    else:
        query = "SELECT acp_id from "+TABLE_MD+ " WHERE sensor_info->>'source'='"+source+"'"

    rows = dbread(query)
    for row in rows:
        slist.append(row[0])
    return slist

def getFeatures(sensor):
    query = "SELECT sensor_info->'features' from "+TABLE_MD+ " WHERE acp_id='"+sensor+"'"

    rows = dbread(query)
    return rows[0][0].split(',')

def getRoomsInCrate(crate_id):
    query = "SELECT * from "+TABLE_BIM+" WHERE bim_info->>'parent_crate_id'='"+crate_id+"'"
    rList = []
    
    rows = dbread(query)
    for row in rows:
        if row[1]['crate_type'] == 'room':            
            rList.append(row[0])
        else:
            rList.extend(getRoomsInCrate(row[0]))
    return rList

def getSensorsInCrate(crate_id):
    roomList = getRoomsInCrate(crate_id)
    sList = []
    if len(roomList) == 0:
        listStr = "'"+crate_id+"'"
    else:
        listStr = ""

        for r in roomList:
            listStr = listStr+"'"+r+"',"
        listStr = listStr[:-1]
    query = "SELECT acp_id from "+TABLE_MD+" WHERE sensor_info->>'parent_crate_id' in ("+listStr+")"

    rows = dbread(query)

    for row in rows:
        sList.append(row[0])

    return sList

def getChildCrates(crate_id, children=inf):
    if children == 0:
        return []
    query = "SELECT * from "+TABLE_BIM+" WHERE bim_info->>'parent_crate_id'='"+crate_id+"'"
    rList = []
    
    rows = dbread(query)
    for row in rows:
        rList.append(row[0])
        if row[1]['crate_type'] != 'room':
            rList.extend(getChildCrates(row[0], children-1))
    return rList

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

def getCratesOnFloor(system, floor_number):
    cList = []

    query = "SELECT crate_id FROM "+TABLE_BIM+" WHERE bim_info->'acp_location'->'f' = '"+str(floor_number)+"' and  bim_info->'acp_location'->'system' = '\""+system+"\"'"
    print(query)
    rows = dbread(query)
    for row in rows:
        cList.append(row[0])
    return cList
    

def getSensorDetails(acp_id):
    query = "SELECT * FROM "+TABLE_MD+" WHERE acp_id = '"+acp_id+"'"
    rows = dbread(query)

    rows[0][1]['acp_id']=rows[0][0]

    return rows[0][1]

def getSensorCount(response):
    cList = []
    for r in response['data']:
        cList.append(r['crate']['crate_id'])

    listStr = ''
    for c in cList:
        listStr = listStr+"'"+c+"',"
    listStr = listStr[:-1]
    
    query = "SELECT acp_id from "+TABLE_MD+" WHERE sensor_info->>'parent_crate_id' in ("+listStr+")"
    
    rows = dbread(query)

    return len(rows)
