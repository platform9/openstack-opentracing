from oslo_log import log
from oslo_serialization import jsonutils

from oslo_middleware import wsgi
from opentracing_instrumentation.request_context import RequestContextManager
from opentracing_instrumentation.client_hooks import install_all_patches
from opentracing_instrumentation.http_server import before_request
from opentracing_instrumentation import span_in_stack_context
from opentracing_instrumentation.request_context import RequestContextManager
from jaeger_client import Config

import webob.dec
import webob.exc
import opentracing

class JaegerMiddleware(wsgi.Middleware):

    def __init__(self, application):
        super(JaegerMiddleware, self).__init__(application)

        config = Config(
          config={ # usually read from some yaml config
            'sampler': {
                'type': 'const',
                'param': 1,
            },
            'logging': True,
            'local_agent': {
                'reporting_host': '127.0.0.1',
                'reporting_port': '6831'
            }
          },
          service_name=self.name,
          validate=True,
        )
        # this call also sets opentracing.tracer
        tracer = config.initialize_tracer()
        install_patches(patchers=['opentracing_instrumentation.client_hooks.sqlalchemy.install_patches',
           'opentracing_instrumentation.client_hooks.urllib.install_patches',
           'opentracing_instrumentation.client_hooks.urllib2.install_patches',
           'opentracing_instrumentation.client_hooks.requests.install_patches',
           'opentracing_instrumentation.client_hooks.tornado_http.install_patches'])
    
    @webob.dec.wsgify()
    def __call__(self, request):
        info = {
           "path": request.path,
           "method": request.method
        }
        with opentracing.tracer.start_span(operation_name=request.path) as span:
            span.log_kv(info)
            with RequestContextManager(span) as ctxt:
                response = request.get_response(self.application)
                return self.process_response(response)