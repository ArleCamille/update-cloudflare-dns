#!/usr/bin/env python
import os
import sys
import urllib.request
from urllib.request import Request
import json
from functools import reduce

#0. check whether there was an environment variable
if 'CLOUDFLARE_EMAIL' not in os.environ:
    print('Please input your email into the environment variable CLOUDFLARE_EMAIL', file=sys.stderr)
    sys.exit(-1)
if 'CLOUDFLARE_KEY' not in os.environ:
    print('Please input CloudFlare API key into the environment variable CLOUDFLARE_KEY', file=sys.stderr)
    sys.exit(-1)
if 'CLOUDFLARE_TARGET' not in os.environ:
    print('Please input domains to update into the environment variable CLOUDFLARE_TARGET', file=sys.stderr)
    sys.exit(-1)

#1. get public IPv4 address
ip = urllib.request.urlopen('https://api.ipify.org').read().decode('utf8')
print(f'My IP address: {ip}')

#2. invoke CloudFlare api
cloudflare_email = os.environ['CLOUDFLARE_EMAIL']
cloudflare_key = os.environ['CLOUDFLARE_KEY']

#2-1. list zones
req_headers = {
    'Content-Type': 'application/json',
    'X-Auth-Email': cloudflare_email,
    'X-Auth-Key': cloudflare_key
}
req = Request('https://api.cloudflare.com/client/v4/zones', headers=req_headers, method='GET')
zones = []

with urllib.request.urlopen(req) as response:
    result = json.loads(response.read().decode('utf8'))
    if not result['success']:
        print('Error while fetching zone info', file=sys.stderr)
        sys.exit(-1)
    for zone_info in result['result']:
        zones.append((zone_info['name'], zone_info['id']))

#2-2. list DNS records for each zone and update appropriately
records = set(map(lambda x: x.strip(), os.environ['CLOUDFLARE_TARGET'].split(',')))
existing_entries = set()

for zone_name, zone_identifier in zones:
    list_req_headers = {
        'Content-Type': 'application/json',
        'X-Auth-Email': cloudflare_email,
        'X-Auth-Key': cloudflare_key,
    }
    list_req = Request(f'https://api.cloudflare.com/client/v4/zones/{zone_identifier}/dns_records', headers=req_headers, method='GET')
    with urllib.request.urlopen(list_req) as list_response:
        list_result = json.loads(list_response.read().decode('utf8'))
        if not list_result['success']:
            print(f'Zone {zone_name} couldn\'t be listed; pass', file=sys.stderr)
            continue
        entries = map(lambda entry: (entry['name'], entry['id'], entry['type']), list_result['result'])
        for entry_name, entry_id, _ in filter(lambda entry: entry[2] == 'A', entries):
            if entry_name not in records:
                pass
            existing_entries.add(entry_name)
            req_body = {'proxied': False, 'type': 'A', 'content': ip, 'name': entry_name, 'ttl': 1}
            req = Request(f'https://api.cloudflare.com/client/v4/zones/{zone_identifier}/dns_records/{entry_id}', data=json.dumps(req_body).encode('utf8'), headers=req_headers, method='PUT')
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode('utf8'))
                if not result['success']:
                    print(f'Failed to update IP address for {entry_name}', file=sys.stderr)
                else:
                    print(f'Updated IP address of domain {entry_name}')

# 2-3. add new entries
def max_zone(subject, previous, current):
    if not subject.endswith(current[0]):
        return previous
    elif previous is None or len(current[0]) > len(previous[0]):
        return current
    else: return previous


records.difference_update(existing_entries)
for entry_name in records:
    longest_zone = reduce(lambda a, b: max_zone(entry_name, a, b), zones, None)
    if longest_zone is None:
        print(f'Couldn\'t find an appropriate zone for domain {entry_name}', file=sys.stderr)
        continue
    print(f'Domain {entry_name} should be managed by {longest_zone[0]}')
    req_body = {'proxied': False, 'name': entry_name, 'content': ip, 'type': 'A', 'ttl': 1}
    zone_identifier = longest_zone[1]
    req = Request(f'https://api.cloudflare.com/client/v4/zones/{zone_identifier}/dns_records', data=json.dumps(req_body).encode('utf8'), headers=req_headers, method='POST')
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode('utf8'))
        if not result['success']:
            print(f'Failed to update IP address for {entry_name}', file=sys.stderr)
        else:
            print(f'Created IP address entry of domain {entry_name}')