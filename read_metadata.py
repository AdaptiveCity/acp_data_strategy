from CONFIG import *
from dbconn import *
import json

def getSources():

    query = "SELECT distinct info->'source' from "+TABLE_MD
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
        query = "SELECT acp_id from "+TABLE_MD+ " WHERE info->>'source'='"+source+"'"

    rows = dbread(query)
    for row in rows:
        slist.append(row[0])
    return slist

def getFeatures(sensor):
    query = "SELECT info->'features' from "+TABLE_MD+ " WHERE acp_id='"+sensor+"'"

    rows = dbread(query)
    return rows[0][0].split(',')