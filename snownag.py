#!/usr/bin/env python2
import json
import os
import requests
import sys
from time import gmtime, strftime

try:
    password = os.environ['NAGIOS__SERVICESSNOWNAG_PASSWORD']
    url = os.environ['NAGIOS__SERVICESSNOWNAG_URL']
    username = os.environ['NAGIOS__SERVICESSNOWNAG_USERNAME']
except KeyError as e:
    print('Unable to obtain {} from environment variables, exiting.'.format(e))
    sys.exit(1)

# Create a more user friendly input
# This equates with (note the blank entry for the host):
# Service: $SERVICESTATE$, $SERVICESTATETYPE$, $SERVICEATTEMPT$, $HOSTNAME$, $SERVICEDESC$, $LONGSERVICEOUTPUT$
# Host: $HOSTSTATE$, $HOSTSTATETYPE$, $HOSTATTEMPT$, $HOSTNAME$, 'Blank Entry', $LONGHOSTOUTPUT$
# TODO: tighten up serviceoutput and longserviceoutput

keys = ['state', 'state_type', 'attempt', 'host_name', 'description', 'long_output']

# Mapping from Nagios levels (keys) to SNOW levels (values)
states = {
    'OK': '0',
    'WARNING': '4',
    'UNKNOWN': '5',
    'CRITICAL': '1',
}

# zip it into a dictionary
nag_output = dict(zip(keys, sys.argv[1:]))

# Only create events on hard states
if nag_output['state_type'] == 'HARD':
    data = {
        'records':
            [
                {
                    'node': nag_output['host_name'],
                    'source': 'Nagios',
                    'metric_name': nag_output['description'],
                    'event_class': 'Nagios Generated Event',
                    'severity': states[nag_output['state']],
                    'additional_info':
                        json.dumps(
                            {
                                'description': nag_output['description'],
                                'output': nag_output['long_output'],
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
