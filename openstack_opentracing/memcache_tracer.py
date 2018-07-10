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


from __future__ import absolute_import

from opentracing.ext import tags as ext_tags
import re
from opentracing_instrumentation import utils
from opentracing_instrumentation.client_hooks._singleton import singleton
from opentracing_instrumentation import get_current_span

try:
    import memcache
except ImportError:  # pragma: no cover
    memcache = None


# regex to match an ipv4 address
IPV4_RE = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$')

METHOD_NAMES = ['get', 'set']
ORIG_METHODS = {}


@singleton
def install_patches():
    """
    Record spans for calls made to memcache
    The code is pretty simple, if memcache is not installed
    skip the patching process, else remember the original methods
    and call them after recording the spans.
    :return:
    """
    if memcache is None:
        return

    for name in METHOD_NAMES:
        ORIG_METHODS[name] = getattr(memcache.Client, name)

    def get(self, name, **kwargs):
        with before_request('get', name):
            return ORIG_METHODS['get'](self, name, **kwargs)

    def set(self, name, value, **kwargs):
        with before_request('set', name):
            return ORIG_METHODS['set'](self, name, value, **kwargs)

    def before_request(cmd, name):
        """
        A common method to record the memcache calls
        :param cmd: either 'get' or 'set'
        :param name: name of the key gettting or setting (Added as a tag)
        :return: the created span
        """
        operation_name = 'memcache:%s' % (cmd)
        span = utils.start_child_span(
            operation_name=operation_name, parent=get_current_span())
        span.set_tag(ext_tags.SPAN_KIND, ext_tags.SPAN_KIND_RPC_CLIENT)

        # TODO: What is the PEER_SERVICE ?
        span.set_tag(ext_tags.PEER_SERVICE, 'memcache')
        span.set_tag('memcache_key', name)
        return span

    for name in METHOD_NAMES:
        setattr(memcache.Client, name, locals()[name])


def reset_patches():
    for name in METHOD_NAMES:
        setattr(memcache.Client, name, ORIG_METHODS[name])
    ORIG_METHODS.clear()
