from flask import Flask, request, render_template,url_for, redirect, jsonify, make_response
from flask_cors import CORS, cross_origin
from os import listdir, path
import json
from collections import defaultdict
import sys
from datetime import datetime
import time

from classes.people_data_api import PeopleDataAPI

DEBUG = True

app = Flask(__name__)
CORS(app)

#####################################
#api/people for People oriented (meta)data
#####################################

@app.route('/get/<person_id>/')
def get_route(person_id):
    global data_api
    path = True if request.args.get('path') == 'true' else False
    response = make_response(data_api.get(person_id, path), 200)
    response.mimetype = "application/json"
    return response

# /get_history/<person_id>/ :
# Similar to '/get/' but returns entire history of metadata for a given person.
@app.route('/get_history/<person_id>/')
def get_history_route(person_id):
    global data_api
    return data_api.get_history(person_id)

# /update/<person_id>/ :
# Updates person object metadata for person 'person_id'
@app.route('/update/<person_id>/', methods = ['POST'])
def update_route(person_id):
    person_metadata = request.json
    global data_api
    return data_api.update(person_id, person_metadata)


####################################################################
#
# Main
#
####################################################################

if __name__ == '__main__':
    print("People API starting...")

    with open('../secrets/settings.json', 'r') as settings_file:
        settings_data = settings_file.read()

    # parse file
    settings = json.loads(settings_data)

    print("People API loaded settings.json")

    data_api = PeopleDataAPI(settings)

    print("Starting People API on {}:{}".format(settings["people_host"],settings["people_port"]))
    app.run( host=settings["people_host"],
             port=settings["people_port"],
             debug=DEBUG)
