from oslo_config import cfg
from oslo_service import wsgi
from paste.deploy import loadapp
import eventlet, time
import requests
import opentracing
import multiprocessing as mp


def start_server(conf, paste_file, port):
    wsgi_app = loadapp('config:%s' % paste_file, 'main')
    server = wsgi.Server(conf, __name__, wsgi_app, host="127.0.0.1", port=port)
    server.start()
    return server

CONF = cfg.CONF
def start_server1():
    eventlet.monkey_patch()
    print "Starting Server 1"
    server = start_server(CONF, '/Users/rparikh/work/misc/openstack-opentracing/openstack_opentracing/test/test-paste.ini', 2326)
    time.sleep(200)


def start_server2():
    eventlet.monkey_patch()
    print "Startng Server 2"
    server2 = start_server(CONF, '/Users/rparikh/work/misc/openstack-opentracing/openstack_opentracing/test/test-paste-2.ini', 2327)
    time.sleep(200)

def perform_tests():
    for count in range(1, 20):
        resp = requests.get('http://127.0.0.1:2326/v1/deadend')
        print resp.text
        resp = requests.get('http://127.0.0.1:2326/v1/forward')
        print resp.text

p1 = mp.Process(target=start_server1, args=())
p1.start()

p2 = mp.Process(target=start_server2, args=())
p2.start()

time.sleep(5)

perform_tests()
time.sleep(5)
p1.terminate()
p2.terminate()
p1.join()
p2.join()
