
from flask import Flask
import requests
app = Flask(__name__)
app.debug = True

@app.route('/v1/deadend', methods=['GET'], strict_slashes= False)
def deadend():
    print "Got request for deadend"
    return "Hello Wrold foo " #% str(resp.text)

@app.route('/v1/forward', methods=['GET'], strict_slashes= False)
def forward():
    print 'Got request for forward, getting data from deadend'
    resp = requests.get('http://127.0.0.1:2327/v1/deadend')
    print "Forwarder made request to deadend got %s" % str(resp.text)
    return "Done with the request %s" % str(resp.text)

@app.route('/v1/check', methods=['GET'], strict_slashes= False)
def check():
    print "Check called"
    resp = requests.get('http://www.google.com')
    return "Check succeeded"

def app_factory(global_config, **local_conf):
    return app

