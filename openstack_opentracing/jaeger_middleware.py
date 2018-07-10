#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from oslo_middleware.base import ConfigurableMiddleware
from opentracing_instrumentation.client_hooks import install_patches
from opentracing_instrumentation.request_context import RequestContextManager
from opentracing_instrumentation.http_server import before_request, WSGIRequestWrapper
from . import tracer_factory
import webob.dec, webob.exc
import logging

logger = logging.getLogger(__name__)

class JaegerMiddleware(ConfigurableMiddleware):

    """
    A middleware meant for OpenStack services that initializes
    spans for *api* OpenStack services.
    """

    tracer = None

    @classmethod
    def factory(cls, global_conf, **local_conf):
        """factory method for paste.deploy
        Here is an example config

        config.logging = False
        config.local_agent.reporting_host = 127.0.0.1
        config.local_agent.reporting_port = 32769
        config.local_agent.sampling_port = 32770
        config.local_agent.sampling_host = 127.0.0.1
        service_name = Server1
        validate = True

        """
        config = tracer_factory. EventletConfig(
          # TODO: Make this more data-driven
          config={
            # Log traces to the log file
            'logging': bool(local_conf['config.logging']),
            'local_agent': {
                # Where to report the samples
                'reporting_host': local_conf['config.local_agent.reporting_host'],
                'reporting_port': int(local_conf['config.local_agent.reporting_port']),

                # A web service that controls the behavior about each service and sampling frequency
                'sampling_host': local_conf['config.local_agent.sampling_host'],
                'sampling_port': int(local_conf['config.local_agent.sampling_port'])
            }
          },
          # Name of the service
          service_name=local_conf['service_name'],
          # Validate the configuration
          validate= bool(local_conf['validate']),
        )
        # this call also sets opentracing.tracer global variable
        tracer = config.initialize_tracer()

        # Monkey patch different code paths
        install_patches(patchers=['opentracing_instrumentation.client_hooks.sqlalchemy.install_patches',
            'opentracing_instrumentation.client_hooks.urllib.install_patches',
            'opentracing_instrumentation.client_hooks.urllib2.install_patches',
            'opentracing_instrumentation.client_hooks.requests.install_patches',
            'opentracing_instrumentation.client_hooks.tornado_http.install_patches',
            'openstack_opentracing.memcache_tracer.install_patches'
        ])
        logger.info("Opentracing initialized for service_name %s", config.service_name)
        return super(JaegerMiddleware, cls).factory(global_conf, **local_conf)

    def __init__(self, application, conf=None):
        super(JaegerMiddleware, self).__init__(application, conf)

    
    @webob.dec.wsgify()
    def __call__(self, request):
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
