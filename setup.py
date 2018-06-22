#!/usr/bin/env python2

from setuptools import setup

setup(
    name = 'openstack_opentracing',
    version = '0.0.1',
    packages = ['openstack_opentracing', 'openstack_opentracing/test'],
    install_requires = [
        'jaeger_client',
        'opentracing_instrumentation',
        'oslo.middleware',
        'oslo.config',
        'oslo.service',
        'flask',
        'futures',
        'requests'
        ],
    scripts = [],
    package_data = {}
)
