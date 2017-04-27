""" Packaging """

from setuptools import find_packages, setup

setup(
    name="consul-deployment-agent-health-checks",
    version="0.0.1",
    description='Consul Deployment Agent - Health Checks',
    long_description="",
    url='https://github.com/trainline/healthcheck-registrar',
    author='Trainline Platform Development',
    author_email='platform.development@thetrainline.com',
    license='Apache 2.0',
    packages=find_packages(exclude=['tests*']),
    install_requires=[
        'docopt',
        'simplejson',
        'tabulate',
        'future',
        'semver',
        'appdirs',
        'progressbar2',
        'envmgr-lib==0.2.1'
    ],
    tests_require=[
        'pytest',
        'mock',
        'nose',
        'nose-parameterized',
        'responses'
    ],
    entry_points={
        'console_scripts': [
            'envmgr-healthchecks=lib.cli:main',
        ],
    },
)
