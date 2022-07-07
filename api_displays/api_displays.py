from flask import Flask, request, render_template,url_for, redirect, jsonify, make_response
from flask_cors import CORS, cross_origin
from os import listdir, path
import json
from collections import defaultdict
import sys
from datetime import datetime
import time

from classes.displays_data_api import DisplaysDataAPI

DEBUG = True

app = Flask(__name__)
CORS(app)

#####################################
#api/people for People oriented (meta)data
#####################################

@app.route('/get/<display_id>/')
def get_route(display_id):
    global data_api
    response = make_response(data_api.get(display_id), 200)
    response.mimetype = "application/json"
    return response

# /get_history/<person_id>/ :
# Similar to '/get/' but returns entire history of metadata for a given person.
@app.route('/get_history/<display_id>/')
def get_history_route(display_id):
    global data_api
    return data_api.get_history(display_id)

# /update/<person_id>/ :
# Updates person object metadata for person 'person_id'
@app.route('/update/<display_id>/', methods = ['POST'])
def update_route(display_id):
    person_metadata = request.json
    global data_api
    return data_api.update(display_id, person_metadata)


####################################################################
#
# Main
#
####################################################################

if __name__ == '__main__':
    print("Display API starting...")

    with open('../secrets/settings.json', 'r') as settings_file:
        settings_data = settings_file.read()

    # parse file
    settings = json.loads(settings_data)

    print("Display API loaded settings.json")

    data_api = DisplaysDataAPI(settings)

    print("Starting Display API on {}:{}".format(settings["displays_host"],settings["displays_port"]))
    app.run( host=settings["displays_host"],
             port=settings["displays_port"],
             debug=DEBUG)
