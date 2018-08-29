from oslo_config import cfg
import eventlet, time
from openstack_opentracing.test.server1 import start_server



def start_server3():
    CONF = cfg.CONF
    print "Starting Server 3"
    server3 = start_server(CONF, '/Users/rparikh/work/misc/openstack-opentracing/openstack_opentracing/test/test-paste-3.ini', 2328)
    time.sleep(2000)

if __name__ == "__main__":
    start_server3()

