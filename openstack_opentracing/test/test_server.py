from oslo_config import cfg
from oslo_service import wsgi
from paste.deploy import loadapp
import eventlet, time
import requests
import opentracing
from openstack_opentracing.jaeger_middleware import JaegerMiddleware


eventlet.monkey_patch()

def start_server(conf, paste_file, port):
    wsgi_app = loadapp('config:%s' % paste_file, 'main')
    server = wsgi.Server(conf, __name__, wsgi_app, host="127.0.0.1", port=port)
    server.start()
    return server

CONF = cfg.CONF
server = start_server(CONF, '/Users/rparikh/work/misc/openstack-opentracing/openstack_opentracing/test/test-paste.ini', 2326)
server2 = start_server(CONF, '/Users/rparikh/work/misc/openstack-opentracing/openstack_opentracing/test/test-paste.ini', 2327)

for count in range(1, 20):
    resp = requests.get('http://127.0.0.1:2326/v1/deadend')
    print resp.text
    resp = requests.get('http://127.0.0.1:2326/v1/forward')
    print resp.text

server.stop()
server2.stop()
time.sleep(2)

opentracing.tracer.close()
time.sleep(2)