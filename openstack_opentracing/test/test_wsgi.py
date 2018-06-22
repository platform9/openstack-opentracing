
from flask import Flask
import requests
app = Flask(__name__)
app.debug = True

@app.route('/v1/deadend', methods=['GET'], strict_slashes= False)
def test1():
    return "Hello Wrold"

@app.route('/v1/forward', methods=['GET'], strict_slashes= False)
def test2():
    resp = requests.get('http://127.0.0.1:2327/v1/deadend')
    return "Done with the request %s" % (resp.text)

def app_factory(global_config, **local_conf):
    return app

