#!/usr/bin/env python3

from setuptools import setup
import os
setup(
    name = 'openstack_opentracing',
    packages = ['openstack_opentracing', 'openstack_opentracing/test'],
    install_requires = [
        'jaeger_client>=3.13.0,<4.0.0',
        'opentracing_instrumentation>=2.4.3,<3.0.0',
        'opentracing>=1.3,<2.0.0',
        'oslo.middleware>=3.0.0',
        'oslo.config>=3.14.0',
        'oslo.service>=1.10.0',
        'oslo.utils>=3.40.2',
        'WebOb>=1.8.0',
        'flask',
        'futures; python_version < "3.0"',
        'requests',
        'pytest'
        ],
    scripts = [],
    package_data = {},
    version='0.1.44.dev2'
)
