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

from jaeger_client.reporter import NullReporter
from jaeger_client import thrift
from jaeger_client.thrift_gen.agent import Agent
from thrift.protocol import TCompactProtocol


class EventletReporter(NullReporter):
    """
    This code is based on the Reporter code that is part of the Jaeger_client package.
    Currently the code base in the jaeger_client is meant to be run only in Tornado environment
    and doesn't work in 'eventlet' based systems like Openstack services.
    This reporter and sampler are supposed to patch by creating new reporter that uses eventlet
    (and are simpler to work with)
    """

    def __init__(self, channel, batch_size=1):
        self._channel = channel
        self._batch_size = batch_size
        self._spans = []
        self.agent = Agent.Client(self._channel, self)
        self._process = None

    def set_process(self, service_name, tags, max_length):
        self._process = thrift.make_process(
            service_name=service_name, tags=tags, max_length=max_length,
        )

    def report_span(self, span):
        self._spans.append(span)
        if len(self._spans) >= self._batch_size:
            self._send_batch()

    def _send_batch(self):
        batch = thrift.make_jaeger_batch(spans=self._spans, process=self._process)
        self._send(batch)
        self._spans = []

    # method for protocol factory
    def getProtocol(self, transport):
        """
        Implements Thrift ProtocolFactory interface
        :param: transport:
        :return: Thrift compact protocol
        """
        return TCompactProtocol.TCompactProtocol(transport)


    def _send(self, batch):
        """
        Send batch of spans out via thrift transport. Any exceptions thrown
        will be caught above in the exception handler of _submit().
        """
        return self.agent.emitBatch(batch)

    def close(self):
        """
        Ensure that all spans from the queue are submitted.
        Returns Future that will be completed once the queue is empty.
        """
        self._send_batch()


