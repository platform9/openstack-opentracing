

import logging

import opentracing
from opentracing.ext import tags as ext_tags
from opentracing_instrumentation import utils
from opentracing_instrumentation.request_context import get_current_span
from opentracing_instrumentation.client_hooks._singleton import singleton
from opentracing_instrumentation.request_context import span_in_stack_context
import six
from opentracing.span import Span
from opentracing import Format

log = logging.getLogger(__name__)


def rpc_context_span_extractor(context):
    """
        Extract and create Span object from context object. Expects
        context object to have span attribute.
    :param context:
    :return: opentracing.span.Span object
    """
    log.debug("In rpc_context_span_extractor...")
    try:
        # If context object doesn't have span, then span cannot be extracted
        if not hasattr(context, 'span'):
            return None
        tracer = opentracing.tracer
        carrier = {}
        log.debug("context object: {}".format(context))
        for key, value in six.iteritems(context.span):
            carrier[key] = value
        parent_ctx = tracer.extract(
            format=Format.TEXT_MAP, carrier=carrier
        )
        span_obj = Span(tracer=tracer, context=parent_ctx)
        log.debug(
            "Span object from rpc_context_span_extractor: {}".format(span_obj))
        return Span(tracer=tracer, context=parent_ctx)
    except:
        log.warn("Error while extracting span object from context")
        return None

@singleton
def install_patches():
    try:
        import oslo_messaging as messaging
    except ImportError:
        # If oslo_messaging cannot be imported, then the project we are
        # instrumenting does not depend on it and we do not need to install
        # the messaging hooks.
        return

    log.info('Instrumenting oslo_messaging methods for tracing')

    _BaseCallContext_call = messaging.rpc.client._BaseCallContext.call
    _BaseCallContext_cast = messaging.rpc.client._BaseCallContext.cast
    _RPCDispatcher_dispatch = messaging.rpc.dispatcher.RPCDispatcher.dispatch

    def call_wrapper(self, ctxt, method, **kwargs):
        """Wraps messaging.rpc.client._BaseCallContext.call"""
        log.debug("RPC CALL method: {}, kwargs: {}".format(method, kwargs))
        span = before_client_send(self.target, ctxt, method, kwargs, 'RPC_CALL')
        resp = _BaseCallContext_call(self, ctxt, method, **kwargs)
        span.finish()
        return resp

    def cast_wrapper(self, ctxt, method, **kwargs):
        """Wraps messaging.rpc.client._BaseCallContext.cast"""
        log.debug("RPC CAST method: {}, kwargs: {}".format(method, kwargs))
        span = before_client_send(self.target, ctxt, method, kwargs, 'RPC_CAST')
        _BaseCallContext_cast(self, ctxt, method, **kwargs)
        span.finish()

    def dispatch_wrapper(self, incoming):
        message = incoming.message
        method = message.get('method')
        namespace = message.get('namespace')
        log.debug("dispatch target method: {}, namespace: {}".format(method,
                                                                    namespace))
        span = before_dispatcher(incoming)

        # Load span to local threading request context
        with span_in_stack_context(span):
            ret = _RPCDispatcher_dispatch(self, incoming)
        log.debug("Dispatch done")

        span.finish()
        return ret

    def before_dispatcher(incoming, tracer=None):
        """
        Attempts to extract a tracing span from incoming request.
        If no tracing context is passed in the headers, or the data
        cannot be parsed, a new root span is started.
        :param incoming: Incoming raw RPC message
        :param tracer: optional tracer instance to use. If not specified
            the global opentracing.tracer will be used.
        :return: returns a new, already started span.
        """
        message = incoming.message
        if tracer is None:  # pragma: no cover
            tracer = opentracing.tracer

        # we need to prepare tags upfront, mainly because RPC_SERVER tag must be
        # set when starting the span, to support Zipkin's one-span-per-RPC model
        tags_dict = {
            ext_tags.SPAN_KIND: ext_tags.SPAN_KIND_RPC_SERVER,
            'rpc_method': message.get('method')
        }

        ctxt = incoming.ctxt
        request_id = ctxt.get('request_id', None)
        if request_id:
            tags_dict['request.id'] = request_id

        if incoming.msg_id:
            # RPC Call
            operation = 'RPC_CALL'
        else:
            # RPC cast
            operation = 'RPC_CAST'

        try:
            carrier = {}
            if 'span' not in ctxt:
                log.warn("span not found in ctxt dict")
                parent_ctx = None
            else:
                if ctxt['span'] is not None:
                    for key, value in six.iteritems(ctxt['span']):
                        carrier[key] = value
                parent_ctx = tracer.extract(
                    format=Format.TEXT_MAP, carrier=carrier
                )
                log.debug("Parent span extracted:{}".format(parent_ctx))
        except Exception as e:
            log.exception('Span extraction failed in before_dispatcher: %s' % e)
            parent_ctx = None

        span = tracer.start_span(
            operation_name=operation,
            child_of=parent_ctx,
            tags=tags_dict)

        return span



    def before_client_send(target, context, method, kwargs, operation):
        """
        A hook to be executed before RPC request is sent from the client side.
        It returns a Span object that can be used as a context manager around
        the actual RPC call implementation, or in case of async callback,
        it needs its `finish()` method to be called explicitly.
        Also, loads the child span context to the service's context object.
        Expects context object to have span attribute.
        :param target: RPC target object
        :param context: context object
        :param method: RPM method name
        :param kwargs: RPM method kwargs
        :return: returns child tracing span encapsulating this request
        """
        # try to extract parent span, using request_context's get_current_span
        # for api service or rpc_context_span_extractor for other services.
        req_context_span = get_current_span()
        rpc_span = rpc_context_span_extractor(context)
        parent_span = req_context_span or rpc_span
        log.debug("req_context_span: {}, rpc_span: {} ... Parent span: {}".
                 format(req_context_span, rpc_span, parent_span))

        span = utils.start_child_span(
            operation_name=operation,
            parent=parent_span
        )

        # Set the needed tags for the span
        span.set_tag(ext_tags.SPAN_KIND, ext_tags.SPAN_KIND_RPC_CLIENT)
        span.set_tag('rpc_method', method)
        span.set_tag('kwargs', str(kwargs))

        request_id = context.request_id
        if request_id:
            span.set_tag('request.id', request_id)

        try:
            carrier = {}
            opentracing.tracer.inject(span_context=span.context,
                                      format=Format.TEXT_MAP,
                                      carrier=carrier)
            log.debug("context object to be used for injecting {}".
                      format(context))
            span_dict = dict()
            for key, value in six.iteritems(carrier):
                span_dict[key] = value
            context.span = span_dict
        except opentracing.UnsupportedFormatException:
            log.warn("Error injecting opentracing span to context")

        return span


    messaging.rpc.client._BaseCallContext.call = call_wrapper
    messaging.rpc.client._BaseCallContext.cast = cast_wrapper
    messaging.rpc.dispatcher.RPCDispatcher.dispatch = dispatch_wrapper