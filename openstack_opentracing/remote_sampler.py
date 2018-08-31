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


from jaeger_client.sampler import Sampler, ErrorReporter
from jaeger_client.sampler import AdaptiveSampler, RateLimitingSampler, RemoteControlledSampler
from jaeger_client.sampler import ProbabilisticSampler, DEFAULT_SAMPLING_INTERVAL, DEFAULT_MAX_OPERATIONS
from jaeger_client.sampler import DEFAULT_SAMPLING_PROBABILITY, OPERATION_SAMPLING_STR, PROBABILISTIC_SAMPLING_STRATEGY
from jaeger_client.sampler import RATE_LIMITING_SAMPLING_STRATEGY, STRATEGY_TYPE_STR
from jaeger_client.sampler import default_logger
from jaeger_client.sampler import get_sampling_probability, get_rate_limit
from threading import Lock
from tornado.httputil import url_concat
import random, json, requests
import eventlet
import httplib

ZERO_SAMPLING_PROBABILITY = 0.0


class EventletRemoteControlledSampler(Sampler):
    """
    Periodically loads the sampling strategy from a remote server.

    This code (and similarly the Reporter code) is based on the jaeger_client code
    which is doesn't work well with 'eventlet' system.

    If the remote server can't be reached it will stop the sampling
    This may not be the best way to work with the sampling, but this
    is a good start
    """
    def __init__(self, service_name, **kwargs):
        """
        :param service_name: name of this application
        :param kwargs: optional parameters
            - init_sampler: initial value of the sampler,
                else ProbabilisticSampler(0.01)
            - sampling_refresh_interval: interval in seconds for polling
              for new strategy
            - logger:
            - error_reporter: ErrorReporter instance
        :param init:
        :return:
        """
        super(EventletRemoteControlledSampler, self).__init__()
        self.service_name = service_name
        self.logger = kwargs.get('logger', default_logger)
        self.sampler = kwargs.get('init_sampler')
        self.sampling_refresh_interval = \
            kwargs.get('sampling_refresh_interval', DEFAULT_SAMPLING_INTERVAL)

        self.max_operations = kwargs.get('max_operations', DEFAULT_MAX_OPERATIONS)

        self.error_reporter = kwargs.get('error_reporter') or ErrorReporter()

        self.local_agent_sampling_host = kwargs.get('sampling_host')
        self.local_agent_sampling_port = kwargs.get('sampling_port')


        self.lock = Lock()
        self.running = True
        self.periodic = None
        self._setup_default_sampling()
        self._next_poll(True)


    def _setup_default_sampling(self):
        """
        Setup default sampling of zero probablistic sampling
        :return:
        """
        with self.lock:
            self.sampler = ProbabilisticSampler(ZERO_SAMPLING_PROBABILITY)
            self.logger.info("Replacing sampler to %s", self.sampler)

    def is_sampled(self, trace_id, operation=''):
        with self.lock:
            return self.sampler.is_sampled(trace_id, operation)

    def _next_poll(self, first_poll=False):
        """
        Bootstrap polling for sampling strategy.

        To avoid spiky traffic from the samplers, we use a random delay
        before the first poll.
        """
        with self.lock:
            if self.running: # This flag will make the polling stop once a close is called
                r = random.Random()
                delay = r.random() * self.sampling_refresh_interval
                eventlet.spawn_after(delay, self._sampling_request)

    def _sampling_request(self):
        """
        Gets the sampling strategy from the upstreadm collector
        :return:
        """
        try:
            # Using httplib because we want to skip the span recording (requests library is monkey patched)
            url = '/sampling?service=%s' % (self.service_name)
            conn = httplib.HTTPConnection(self.local_agent_sampling_host, port=self.local_agent_sampling_port)
            conn.request('GET', url)
            text = conn.getresponse().read().decode('utf-8')
            #response = requests.get(url)
            sampling_strategies_response = json.loads(text)
            self._update_sampler(sampling_strategies_response)
        except:
            # Expect this to be the normal case use the error_reporter to only log it every 15 min
            self.error_reporter.error(
                'Fail to get or parse sampling strategy '
                'from jaeger-agent, stopping the sampling')
            self._setup_default_sampling()
        finally:
            self._next_poll()


    def _update_sampler(self, response):
        with self.lock:
            try:
                if response.get(OPERATION_SAMPLING_STR):
                    self._update_adaptive_sampler(response.get(OPERATION_SAMPLING_STR))
                else:
                    self._update_rate_limiting_or_probabilistic_sampler(response)
            except Exception as e:
                self.error_reporter.error(
                    'Fail to update sampler'
                    'from jaeger-agent: %s [%s]', e, response)

    def _update_adaptive_sampler(self, per_operation_strategies):
        """
        This function is not tested so ignore it for now
        :param per_operation_strategies:
        :return:
        """
        if isinstance(self.sampler, AdaptiveSampler):
            self.sampler.update(per_operation_strategies)
        else:
            self.sampler = AdaptiveSampler(per_operation_strategies, self.max_operations)

    def _update_rate_limiting_or_probabilistic_sampler(self, response):
        s_type = response.get(STRATEGY_TYPE_STR)
        if s_type == PROBABILISTIC_SAMPLING_STRATEGY:
            sampling_rate = get_sampling_probability(response)
            new_sampler = ProbabilisticSampler(rate=sampling_rate)
        elif s_type == RATE_LIMITING_SAMPLING_STRATEGY:
            mtps = get_rate_limit(response)
            if 0 <= mtps < 500:
                new_sampler = RateLimitingSampler(max_traces_per_second=mtps)
            else:
                raise ValueError(
                    'Rate limiting parameter not in [0, 500] range: %s' % mtps)
        else:
            raise ValueError('Unsupported sampling strategy type: %s' % s_type)

        if self.sampler != new_sampler:
            self.sampler = new_sampler
            self.logger.info("Replacing sampler to %s", self.sampler)


    def close(self):
        """
        Stop the sampling, set the flag
        :return:
        """
        with self.lock:
            self.running = False
