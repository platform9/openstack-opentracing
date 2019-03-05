from . import tracer_factory
import logging
from opentracing_instrumentation.client_hooks import install_patches
from oslo_config import cfg

logger = logging.getLogger(__name__)

opentracing_group = cfg.OptGroup(
    'opentracing',
    title='opentracing Options',
    help="""
Options under this group are used to define How to access Opentracing server
""",
)

ALL_OPTS = [
    cfg.StrOpt(
        'reporting_host',
        default='127.0.0.1',
        help="""
    Reporting Host
    """),
    cfg.IntOpt(
        'reporting_port',
        default=6831,
        help="""
    Reporting port
    """),
    cfg.StrOpt(
        'sampling_host',
        default='127.0.0.1',
        help="""
    Sampling Host
    """),
    cfg.IntOpt(
        'sampling_port',
        default=5778,
        help="""
    Sampling Port
    """)
]


def register_opts(conf):
    conf.register_group(opentracing_group)
    conf.register_opts(ALL_OPTS, group=opentracing_group)


def initialize_jaeger_tracer(CONF, service_name):
    """Initializer function to be called at the beginning of service starts.
    :param CONF: oslo_config object from service
    :param service_name: name of the service to be seen in jaeger UI
    """
    logger.info("Registering all config components for opentracing")
    register_opts(CONF)

    logger.info(
        "Initializing jaeger tracer for service: {}".format(service_name))

    config = tracer_factory.EventletConfig(
      config={
        # Log traces to the log file
        'logging': True,
        'local_agent': {
            # Where to report the samples
            'reporting_host': CONF.opentracing.reporting_host,
            'reporting_port': int(CONF.opentracing.reporting_port),

            # A web service that controls the behavior about each service and sampling frequency
            'sampling_host': CONF.opentracing.sampling_host,
            'sampling_port': int(CONF.opentracing.sampling_port)
        }
      },
      # Name of the service
      service_name=service_name,
      # Validate the configuration
      validate=True
    )
    # this call also sets opentracing.tracer global variable
    tracer = config.initialize_tracer()

    # Monkey patch different code paths
    install_patches(patchers=['opentracing_instrumentation.client_hooks.sqlalchemy.install_patches',
        'opentracing_instrumentation.client_hooks.urllib.install_patches',
        'opentracing_instrumentation.client_hooks.urllib2.install_patches',
        'opentracing_instrumentation.client_hooks.requests.install_patches',
        'opentracing_instrumentation.client_hooks.tornado_http.install_patches',
        'openstack_opentracing.memcache_tracer.install_patches',
        'openstack_opentracing.instrumentation.oslo_rpc.install_patches'
    ])
    logger.info("Opentracing initialized for service_name %s", service_name)
