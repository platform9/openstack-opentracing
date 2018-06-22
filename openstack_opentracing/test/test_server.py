from oslo_config import cfg
from oslo_service import wsgi
from paste.deploy import loadapp
import eventlet

eventlet.monkey_patch()


def start_server(conf, paste_file):
    wsgi_app = loadapp('config:%s' % paste_file, 'main')
    server = wsgi.Server(conf, __name__, wsgi_app, host="127.0.0.1", port=2326)
    server.start()
    return server

CONF = cfg.CONF
server = start_server(CONF, '/Users/rparikh/work/misc/openstack-opentracing/openstack_opentracing/test/test-paste.ini')
eventlet.sleep(200000)