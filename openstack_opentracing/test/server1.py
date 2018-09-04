from oslo_config import cfg
import eventlet, time
from paste.deploy import loadapp
eventlet.monkey_patch()
from oslo_service import wsgi
import os
from eventlet import greenthread
import logging
from logging.config import dictConfig

logging_config = dict(
    version = 1,
    formatters = {
        'f': {'format':
              '%(asctime)s %(name)-12s %(levelname)-8s %(process)d %(message)s'}
        },
    handlers = {
        'h': {'class': 'logging.StreamHandler',
              'formatter': 'f',
              'level': logging.DEBUG}
        },
    root = {
        'handlers': ['h'],
        'level': logging.DEBUG,
        },
)

logging.config.dictConfig(logging_config)

def start_server(conf, paste_file, port):
    eventlet.monkey_patch()
    wsgi_app = loadapp('config:%s' % paste_file, 'main')
    server = wsgi.Server(conf, __name__, wsgi_app, host="127.0.0.1", port=port)
    server.start()
    return server

def hello():
    print "Hello "

def foo():
    greenthread.spawn_after(10, hello)

def start_server1():
    CONF = cfg.CONF
    print "Starting Server 1"
    server1 = start_server(CONF,
                           '/Users/rparikh/work/misc/openstack-opentracing/openstack_opentracing/test/test-paste.ini',
                           2326)
    time.sleep(20)
    greenthread.spawn(foo)
    if 0 == os.fork() :
        print "Child Process "
    else:
        print "Parent Process "

    time.sleep(2000)

if __name__ == "__main__":
    start_server1()


