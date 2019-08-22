#!/usr/bin/env python2

import argparse
import json
import os
import requests
import sys
from time import gmtime, strftime

__version__ = '0.0.1'

parser = argparse.ArgumentParser(description='Convert Nagios Events to SNOW Events')
parser.add_argument('attempt', help='The $SERVICEATTEMPT$ or $HOSTATTEMPT$')
parser.add_argument('host-name', help='The $HOSTNAME$')
parser.add_argument('state', help='The $SERVICESTATE$ or $HOSTSTATE$')
parser.add_argument('state-type', help='The $SERVICESTATETYPE$ or $HOSTSTATETYPE$')
parser.add_argument('output', nargs='*', help='The SERVICEOUTPUT$ or $HOSTOUTPUT$')
parser.add_argument('-d', '--description',
                    help='The $SERVICEDESC$ note there is no host equivalent',
                    default='')
parser.add_argument('--version', action='version', version='%(prog)s {}'.format(__version__))

args = parser.parse_args()

try:
    password = os.environ['NAGIOS__SERVICESSNOWNAG_PASSWORD']
    url = os.environ['NAGIOS__SERVICESSNOWNAG_URL']
    username = os.environ['NAGIOS__SERVICESSNOWNAG_USERNAME']
except KeyError as e:
    print('Unable to obtain {} from environment variables, exiting.'.format(e))
    sys.exit(1)

# Mapping from Nagios levels (keys) to SNOW levels (values)
states = {
    'OK': '0',
    'WARNING': '4',
    'UNKNOWN': '5',
    'CRITICAL': '1',
}

# Only create events on hard states
if args['state-type'] == 'HARD':
    data = {
        'records':
            [
                {
                    'node': args['host-name'],
                    'source': 'Nagios',
                    'metric_name': args['description'],
                    'event_class': 'Nagios Generated Event',
                    'severity': states[args['state']],
                    'additional_info':
                        json.dumps(
                            {
                                'description': args['description'],
                                'output': args['output'],
                            }
                        ),
                    'time_of_event': strftime("%Y-%m-%d %H:%M:%S", gmtime())
                }
            ]
    }

    full_url = '{}/api/global/em/jsonv2'.format(url)

    try:
        response = requests.post(full_url,auth=(username, password), json=data, timeout=2)
    except (requests.ConnectionError, requests.Timeout):
        print('The connection to {} failed!'.format(full_url))
        sys.exit(1)

    try:
        response.raise_for_status()
    except requests.HTTPError:
        print('HTTP Error: {} occurred!'.format(response.status_code))
        sys.exit(1)
    else:
        sys.exit(0)

else:
    sys.exit(0)
