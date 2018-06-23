# openstack-opentracing
This library provides a simple (alpha quality) implementation of a wsgi middleware that can be inserted into
OpenStack APIs and can provide rudimentary tracing.

## How to

### Install Jager tracing all in one
docker run --name jaeger  -p 5775:5775/udp -p 5778:5778 -p 14268:14268 -p 6831:6831/udp -p 6832:6832/udp -p 16686:16686 jaegertracing/all-in-one:latest

### Install openstack-opentracing

Activate your virtualenv

```bash
source /opt/pf9/nova/bin/activate
cd /opt/pf9/nova/bin/
./python ./pip install git+https://github.com/platform9-incubator/openstack-opentracing.git
```

### Configure your service

Edit your paste.ini file and insert a new filter and add the filter to the pipeline
```bash
[filter:jaeger_v1]
paste.filter_factory = openstack_opentracing.jaeger_middleware:JaegerMiddleware.factory
config.sampler.type = const
config.sampler.param = 1
config.logging = True
config.local_agent.reporting_host = 127.0.0.1
config.local_agent.reporting_port = 6831
service_name = keystone
validate = True

[pipeline:public_api]
# The last item in this pipeline must be public_service or an equivalent
# application. It cannot be a filter.
pipeline = sizelimit url_normalize request_id build_auth_context jaeger_v1 token_auth admin_token_auth json_body ec2_extension user_crud_extension pf9_mfa_auth_extension_v2 public_service
```

### Restart your service

```bash
sudo service openstack-nova-api restart
```

## Check the UI

Connect to http://<ip-address>:16686/ to check the UI.
Make some nova-api requests and your tracing will show up automatically

I SSH into the DU and use the port forwarding
```bash
ssh -L 14268:127.0.0.1:14268 -L 16686:127.0.0.1:16686 pf9-test.platform9.net
```

# Code
There is only one file which is interesting jaeger_middleware, which provides the middleware.
Check the test directory for a working example of a distributed tracing example which uses the middleware and uses oslo.* libraries. This will give you a good starting point.

# TODO
Many many things
* Tracing between services is not working, probably because of some monkey patching gone wrong, this needs to be debugged
* Jaeger client library are tornado based and don't like eventlet, there is a lot of hacking in jaeger_middleware which can be immensly simplified.
* the sampling is pretty nasty, it can collect ton of data in a very duration, the sampling should be probablistic and 'remote controlled': this needs to be investigated
* how to run a jaeger server ?? (not the simple all-in-one).
