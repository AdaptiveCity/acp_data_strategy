from CONFIG import *
from dbconn import *
import json

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
