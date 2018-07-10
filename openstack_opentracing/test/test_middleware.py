from oslo_log import log
from oslo_serialization import jsonutils

from oslo_middleware.base import ConfigurableMiddleware
import webob.dec
import webob.exc
import requests

class ExampleMiddleware(ConfigurableMiddleware):

    def __init__(self, application, conf=None):
        super(ExampleMiddleware, self).__init__(application, conf)

    @webob.dec.wsgify()
    def __call__(self, request):
        try:
            print "Middleware called"
            resp = requests.get('http://127.0.0.1:2328/v1/check')
            if not resp.status_code == 200:
                print "Example Error %s " % str(resp.status_code)
            else:
                print "Example Passed Test: %s" % str(resp.text)
            response = request.get_response(self.application)
            return self.process_response(response)
        except:
            # TODO: Use logging instead of stdout
            import sys, traceback
            e = sys.exc_info()[0]
            print "Error: %s" % str(e)
            traceback.print_exc(file=sys.stdout)
            raise