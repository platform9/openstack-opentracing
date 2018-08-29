from oslo_config import cfg
import eventlet, time
from openstack_opentracing.test.server1 import start_server



def start_server2():
    CONF = cfg.CONF
    print "Starting Server 2"
    server2 = start_server(CONF, '/Users/rparikh/work/misc/openstack-opentracing/openstack_opentracing/test/test-paste-2.ini', 2327)
    time.sleep(2000)

if __name__ == "__main__":
    start_server2()

