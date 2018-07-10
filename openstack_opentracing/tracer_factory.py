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

from jaeger_client import Config

from jaeger_client.reporter import CompositeReporter, LoggingReporter
from . import remote_sampler, eventlet_tracer
import logging


logger = logging.getLogger(__name__)


class EventletConfig(Config):

    """
    Like few other classes in this directory this is an extension of jaeger_client library
    and deals with making 'eventlet' service work with jaeger_client code.
    """
    def __init__(self, config, service_name, validate):
        super(EventletConfig, self).__init__(config, service_name=service_name, validate=validate)

    @property
    def local_agent_sampling_host(self):
        try:
            return self.local_agent_group()['sampling_host']
        except:
            return '127.0.0.1'


    def new_tracer(self, io_loop=None):
        """
        Create a new Jaeger Tracer based on the passed `jaeger_client.Config`.
        Does not set `opentracing.tracer` global variable.
        """
        channel = self._create_local_agent_channel(io_loop=io_loop)
        sampler = self.sampler
        if sampler is None:
            sampler = remote_sampler.EventletRemoteControlledSampler(
                service_name=self.service_name,
                logger=logger,
                error_reporter=self.error_reporter,
                sampling_refresh_interval=self.sampling_refresh_interval,
                max_operations=self.max_operations,
                sampling_host=self.local_agent_sampling_host,
                sampling_port=self.local_agent_sampling_port
            )
        logger.info('Using sampler %s', sampler)

        reporter = eventlet_tracer.EventletReporter(channel=channel)

        if self.logging:
            reporter = CompositeReporter(reporter, LoggingReporter(logger))

        return self.create_tracer(
            reporter=reporter,
            sampler=sampler,
        )
