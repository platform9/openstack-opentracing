#!/usr/bin/env python2

from setuptools import setup
import os
setup(
    name = 'openstack_opentracing',
    packages = ['openstack_opentracing', 'openstack_opentracing/test'],
    setup_requires=['pbr'],
    install_requires = [
        'jaeger_client==3.10.0',
        'opentracing_instrumentation==2.4.1',
        'opentracing==1.3.0',
        'oslo.middleware>=3.0.0',
        'oslo.config>=3.14.0',
        'oslo.service>=1.10.0',
        'flask>=0.10.0',
        'futures',
        'requests>=2.10.0'
        ],
    scripts = [],
    package_data = {},
    pbr=True
)
