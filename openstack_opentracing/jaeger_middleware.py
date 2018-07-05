from oslo_log import log
from oslo_serialization import jsonutils

from oslo_middleware.base import ConfigurableMiddleware
from opentracing_instrumentation.client_hooks import install_patches
from opentracing_instrumentation.request_context import RequestContextManager
from opentracing_instrumentation.http_server import before_request, WSGIRequestWrapper
from jaeger_client import Config
from jaeger_client.reporter import Reporter, CompositeReporter
from . import eventlet_tracer
import webob.dec
import webob.exc
import opentracing

def _start_reporter_loop(tracer, config):
    if not tracer:
        return

    channel = config._create_local_agent_channel(None)
    direct_reporters = []
    if isinstance(tracer.reporter, CompositeReporter):
        reporters = []
        for reporter in tracer.reporter.reporters:
            reporters.append(reporter)
        eventlet_reporter = eventlet_tracer.EventletReporter(channel=channel)
        reporters.append(eventlet_reporter)
        tracer.reporter.reporters = reporters
        eventlet_reporter.set_process(
            service_name=tracer.service_name,
            tags=tracer.tags,
            max_length=tracer.max_tag_value_length,
        )
        print "Registering the service name %s " % (tracer.service_name)

    for reporter in direct_reporters:
        reporter._consume_queue()

class JaegerMiddleware(ConfigurableMiddleware):

    tracer = None

    @classmethod
    def factory(cls, global_conf, **local_conf):
        """factory method for paste.deploy
        config.sampler.type = const
        config.sampler.param = 1
        config.logging = True
        config.local_agent.reporting_host = 127.0.0.1
        config.local_agent.reporting_port = 6831
        service_name = TestServer
        validate = True
        """
        config = Config(
          config={ # usually read from some yaml config
            'sampler': {
                'type': local_conf['config.sampler.type'],
                'param': int(local_conf['config.sampler.param']),
            },
            'logging': bool(local_conf['config.logging']),
            'local_agent': {
                'reporting_host': local_conf['config.local_agent.reporting_host'],
                'reporting_port': int(local_conf['config.local_agent.reporting_port'])
            }
          },
          service_name=local_conf['service_name'],
          validate= bool(local_conf['validate']),
        )
        # this call also sets opentracing.tracer
        tracer = config.initialize_tracer()
        install_patches(patchers=['opentracing_instrumentation.client_hooks.sqlalchemy.install_patches',
            'opentracing_instrumentation.client_hooks.urllib.install_patches',
            'opentracing_instrumentation.client_hooks.urllib2.install_patches',
            'opentracing_instrumentation.client_hooks.requests.install_patches',
            'opentracing_instrumentation.client_hooks.tornado_http.install_patches'
        ])
        _start_reporter_loop(tracer, config)
        return super(JaegerMiddleware, cls).factory(global_conf, **local_conf)

    def __init__(self, application, conf=None):
        super(JaegerMiddleware, self).__init__(application, conf)

    
    @webob.dec.wsgify()
    def __call__(self, request):
        try:
            new_request = WSGIRequestWrapper.from_wsgi_environ(request.environ)
            info = {
                "path": request.path,
                "method": request.method
            }
            with before_request(new_request) as span:
                span.log_kv(info)
                with RequestContextManager(span) as ctxt:
                    response = request.get_response(self.application)
                    return self.process_response(response)
        except:
            # TODO: Use logging instead of stdout
            import sys,traceback
            e = sys.exc_info()[0]
            print "Error: %s" % str(e)
            traceback.print_exc(file=sys.stdout)
            raise