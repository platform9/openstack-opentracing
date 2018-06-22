
from flask import Flask

app = Flask(__name__)
app.debug = True

@app.route('/v1/test1', methods=['GET'], strict_slashes= False)
def test1():
    return "Hello Wrold"

@app.route('/v1/test2', methods=['GET'], strict_slashes= False)
def test2():
    return "Hello World2"

def app_factory(global_config, **local_conf):
    return app

