from flask import Flask, request, render_template,url_for, redirect, jsonify, make_response
from flask_cors import CORS, cross_origin
from os import listdir, path
import json
import base64

from collections import defaultdict
import sys
from datetime import datetime
import time
from flask_wtf.csrf import CSRFProtect

from classes.space_api import SpaceDataAPI

DEBUG = True

app = Flask(__name__)
CORS(app)

csrf = CSRFProtect(app)
app.config['SECRET_KEY'] = "secretkey"
app.config['WTF_CSRF_SECRET_KEY'] = "secretkey"

csrf.init_app(app)

####################################################################
# Flask routes
####################################################################

#################################
#api/space for SVG related things
#################################

# Get SVG for selected crate (and children)
@app.route('/get_bim/<crate_id>/', defaults={'children': 0})
@app.route('/get_bim/<crate_id>/<children>/')
def get_svg_by_crate(crate_id,children):
    global space_api
    if str(children)=='all': #or type(children)!=int:
        children=999
    else:
        try:
            children=int(children)
        except:
            children=999
    response_string = space_api.get_crate_svg(crate_id, children)
    print("space_render get_svg_by_crate {} returning:\n{}\n".format(crate_id, response_string))
    response = make_response(response_string, 200)
    response.mimetype = "text/xml"
    return response

# As above, but returns JSON not XML
@app.route('/get_bim_json/<crate_id>/', defaults={'children': 0})
@app.route('/get_bim_json/<crate_id>/<children>/')
def get_svg_by_crate_json(crate_id,children):
    global space_api
    if str(children)=='all': #or type(children)!=int:
        children=999
    else:
        try:
            children=int(children)
        except:
            children=999
    svg_string = space_api.get_crate_svg(crate_id, children)
    svg_bytes = svg_string.encode('utf-8')
    b64_bytes = base64.b64encode(svg_bytes)
    b64_string = b64_bytes.decode('utf-8')
    response_string = f'{{ "svg_encoded": "{b64_string}" }}'
    response = make_response(response_string, 200)
    response.mimetype = "application/json"
    return response

#DEBUG need to be clear if this is the "f" propery of an acp_location ?
@app.route('/get_floor_number_json/<coordinate_system>/<floor_number>/')
def get_floor_number_json_route(coordinate_system,floor_number):
    global space_api
    svg_string = space_api.get_floor_number(coordinate_system, floor_number)
    svg_bytes = svg_string.encode('utf-8')
    b64_bytes = base64.b64encode(svg_bytes)
    b64_string = b64_bytes.decode('utf-8')
    print(b64_string)
    response_string = f'{{ "svg_encoded": "{b64_string}" }}'
    response = make_response(response_string, 200)
    response.mimetype = "application/json"
    return response

#DEBUG change to get/bim_floor
#DEBUG need to be clear if this is the "f" propery of an acp_location ?
@app.route('/get_floor_number/<coordinate_system>/<floor_number>/')
def get_floor_number_route(coordinate_system,floor_number):
    global space_api
    response_string = space_api.get_floor_number(coordinate_system, floor_number)
    response = make_response(response_string, 200)
    response.mimetype = "text/xml"
    return response

#@app.route('get/sensor/<acp_id>)

####################################################################
#
# Main
#
####################################################################

if __name__ == '__main__':
    print("SpaceAPI starting...")

    with open('../secrets/settings.json', 'r') as settings_file:
        settings_data = settings_file.read()

    # parse file
    settings = json.loads(settings_data)

    print("SpaceRender loaded settings.json")

    space_api = SpaceDataAPI(settings)

    app.run( host=settings["space_host"],
             port=settings["space_port"],
             debug=DEBUG)
