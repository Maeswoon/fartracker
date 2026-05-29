#!/usr/bin/env python3
"""Simulate a launch trajectory by posting points at 100 ft/s for 100 seconds.

Usage: python scripts/sim_trajectory.py <team_identifier> [--base-url http://localhost:8000]
"""
import argparse
import json
import sys
import time
import urllib.request
import urllib.error
from http.cookiejar import CookieJar

MAP_CENTER_LAT = 35.34715
MAP_CENTER_LON = -117.80898
DEFAULT_BASE = 'http://localhost:8000'


def get_token(base, username, password):
    url = f'{base}/api/token/'
    data = json.dumps({'username': username, 'password': password}).encode()
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))
    resp = opener.open(req)
    return opener


def put_trajectory(opener, base, team_id, points):
    url = f'{base}/api/team_tracking/trajectories/{team_id}'
    data = json.dumps({'points': points}).encode()
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='PUT')
    resp = opener.open(req)
    return json.loads(resp.read())


def post_points(opener, base, team_id, pts):
    url = f'{base}/api/team_tracking/trajectories/{team_id}'
    data = json.dumps({'points': pts}).encode()
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
    resp = opener.open(req)
    return json.loads(resp.read())


def main():
    parser = argparse.ArgumentParser(description='Simulate a launch trajectory')
    parser.add_argument('team_id', help='Team identifier (e.g. AH050UVU)')
    parser.add_argument('--base-url', default=DEFAULT_BASE, help=f'Base URL (default: {DEFAULT_BASE})')
    parser.add_argument('--username', default='admin', help='Login username')
    parser.add_argument('--password', default='admin', help='Login password')
    args = parser.parse_args()

    print(f'Authenticating as {args.username}...')
    try:
        opener = get_token(args.base_url, args.username, args.password)
    except urllib.error.HTTPError as e:
        print(f'Login failed: {e.code} {e.reason}')
        sys.exit(1)
    print('Authenticated.')

    print(f'Clearing trajectory for {args.team_id}...')
    put_trajectory(opener, args.base_url, args.team_id, [])
    print('Cleared.')

    print(f'Posting 100 points (1/sec, 100 ft/sec ascent)...')
    for i in range(0, 100):
        alt = i * 100
        lat = MAP_CENTER_LAT + i * 0.0001
        lon = MAP_CENTER_LON + i * 0.0001
        pts = [[lat, lon, alt]]
        try:
            post_points(opener, args.base_url, args.team_id, pts)
        except urllib.error.HTTPError as e:
            print(f'\nPost failed at point {i+1}: {e.code} {e.reason}')
            sys.exit(1)
        print(f'  Point {i+1}/100: alt={alt} ft  lat={lat:.5f}  lon={lon:.5f}', end='\r')
        time.sleep(1)
    print('\nDone.')


if __name__ == '__main__':
    main()
