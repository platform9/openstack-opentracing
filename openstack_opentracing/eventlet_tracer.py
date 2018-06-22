
from jaeger_client.reporter import NullReporter
from jaeger_client import thrift
from jaeger_client.thrift_gen.agent import Agent

from thrift.protocol import TCompactProtocol


class EventletReporter(NullReporter):


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
        if len(self._spans) > self._batch_size:
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


