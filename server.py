"""
Python Flask WebApp Auth0 client-rules example
"""
from functools import wraps
import json
from os import environ as env

from dotenv import load_dotenv, find_dotenv
from flask import Flask
from flask import jsonify
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for
from flask_oauthlib.client import OAuth
from six.moves.urllib.parse import urlencode

from client import Client

import re 
import requests
import constants

# Get all environment data 
ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

AUTH0_CALLBACK_URL = env.get(constants.AUTH0_CALLBACK_URL)
AUTH0_CLIENT_ID = env.get(constants.AUTH0_CLIENT_ID)
AUTH0_CLIENT_SECRET = env.get(constants.AUTH0_CLIENT_SECRET)
AUTH0_CLIENT_ID_MNGNMT_API = env.get(constants.AUTH0_CLIENT_ID_MNGNMT_API)
AUTH0_CLIENT_SECRET_MNGNMT_API = env.get(constants.AUTH0_CLIENT_SECRET_MNGNMT_API)
AUTH0_AUDIENCE_MNGNMT_API = env.get(constants.AUTH0_AUDIENCE_MNGNMT_API)
GRANT_TYPE = env.get(constants.GRANT_TYPE)
AUTH0_DOMAIN = env.get(constants.AUTH0_DOMAIN)
AUTH0_AUDIENCE = env.get(constants.AUTH0_AUDIENCE)
if AUTH0_AUDIENCE is '':
    AUTH0_AUDIENCE = 'https://' + AUTH0_DOMAIN + '/userinfo'

APP = Flask(__name__, static_url_path='/public', static_folder='./public')
APP.secret_key = constants.SECRET_KEY
APP.debug = True

# Format error response and append status code.
class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


@APP.errorhandler(AuthError)
def handle_auth_error(ex):
    response = jsonify(ex.error)
    response.status_code = ex.status_code
    return response


@APP.errorhandler(Exception)
def handle_auth_error(ex):
    response = jsonify(message=ex.message)
    return response

oauth = OAuth(APP)

auth0 = oauth.remote_app(
    'auth0',
    consumer_key=AUTH0_CLIENT_ID,
    consumer_secret=AUTH0_CLIENT_SECRET,
    request_token_params={
        'scope': 'openid profile',
        'audience': AUTH0_AUDIENCE
    },
    base_url='https://%s' % AUTH0_DOMAIN,
    access_token_method='POST',
    access_token_url='/oauth/token',
    authorize_url='/authorize',
)

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if constants.PROFILE_KEY not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated

def extract_app_name(script):
    index_of_context = re.findall('\(.*?\)', script)[1]
    context_type = re.findall('\w+\s', index_of_context)[0]
    app_name = re.findall(r'\'(.+?)\'',index_of_context)[0]
    return { 'type': context_type, 'name': app_name }


# Controllers API
@APP.route('/')
def home():
    return render_template('home.html')


@APP.route('/callback')
def callback_handling():
    resp = auth0.authorized_response()
    if resp is None:
        raise AuthError({'code': request.args['error'],
                         'description': request.args['error_description']}, 401)

    # authenticate user
    url = 'https://' + AUTH0_DOMAIN + '/userinfo'
    headers = {'authorization': 'Bearer ' + resp['access_token']}
    resp = requests.get(url, headers=headers)
    userinfo = resp.json()

    session[constants.JWT_PAYLOAD] = userinfo

    session[constants.PROFILE_KEY] = {
        'user_id': userinfo['sub'],
        'name': userinfo['name'],
    }

    return redirect('/dashboard')


@APP.route('/login')
def login():
    return auth0.authorize(callback=AUTH0_CALLBACK_URL)


@APP.route('/logout')
def logout():
    session.clear()
    params = {'returnTo': url_for('home', _external=True), 'client_id': AUTH0_CLIENT_ID}
    return redirect(auth0.base_url + '/v2/logout?' + urlencode(params))


@APP.route('/dashboard')
@requires_auth
def dashboard():
    return render_template('dashboard.html',
                           userinfo=session[constants.PROFILE_KEY])
                          
@APP.route('/viewlist')
@requires_auth
def viewlist():
    
    # get access token from Auth0 for mngnment api
    base_url = "https://" + AUTH0_DOMAIN

    mngmnt_api_data = {'client_id':AUTH0_CLIENT_ID_MNGNMT_API,
                       'client_secret':AUTH0_CLIENT_SECRET_MNGNMT_API,
                       'audience': AUTH0_AUDIENCE_MNGNMT_API,
                       'grant_type': 'client_credentials'}

    req = requests.post(base_url + "/oauth/token", data=mngmnt_api_data)
    access_data = req.json()
    access_token = access_data['access_token']

    # get all rules using the access token 
    headers = {'authorization': 'Bearer ' + access_token}
    req = requests.get(base_url + "/api/v2/rules?fields=script,name", headers=headers)
    rules_data = req.json()

    # get all clients 
    req = requests.get(base_url + "/api/v2/clients?fields=name,client_id", headers=headers)
    client_data = req.json()

    # format client data from api into a list
    client_list = {}

    for x in client_data[:-1]:
        new_client = Client(x['name'], x['client_id'])
        client_list[new_client] = [" "]
        
    # add rules to client list 
    for rule in rules_data:
        context_data = extract_app_name(rule['script'])
        app_rule_type = context_data['type']
        app_name = context_data['name']
        for key, value in client_list.items():
            if app_rule_type=="clientName ":
                search_key = key.name
            else:
                search_key = key.id
            if app_name==search_key:
                value.append(str(rule['name']))
                break  
        # end of client_list loop
    # end of rules_data loop       

    session[constants.RULES_PAYLOAD] = rules_data

    session[constants.CLIENTS_PAYLOAD] = client_data

    return render_template('viewlist.html',
                           client_list=client_list)

if __name__ == "__main__":
    APP.run(host='0.0.0.0', port=env.get('PORT', 3000))
