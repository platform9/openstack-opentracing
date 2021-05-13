#!/usr/bin/env python3

from setuptools import setup
import os
setup(
    name = 'openstack_opentracing',
    packages = ['openstack_opentracing', 'openstack_opentracing/test'],
    install_requires = [
        'jaeger_client==4.4.0',
        'opentracing_instrumentation>=3.3,<4',
        #'opentracing>=2.1,<3.0',
        'opentracing>=2.1,<3.0',
        'oslo.middleware>=3.0.0',
        'oslo.config>=3.14.0',
        'oslo.service>=1.10.0',
        'flask',
        #'flask>=0.10.0',
        #'futures',
        'futures; python_version < "3.0"',
        'requests',
        #'requests>=2.10.0',
        'pytest'
        ],
    scripts = [],
    package_data = {},
    version='0.3.44'
)
