#!/usr/bin/env python3
"""Test realtime pipeline: login, post events, listen on websocket.

Usage:
  python tools/test_realtime.py --api-url http://127.0.0.1:8000 --username admin --password Admin@12345

The script will:
 - log in and obtain a token
 - pick the first camera if no --camera-id provided
 - POST three events (exact match, near-miss, low-confidence)
 - connect to the WS `/ws/dashboard?token=...` and print messages for 10s
"""
import argparse
import asyncio
import json
import time
from datetime import datetime, timezone

import requests
import websockets


def login(api_url, username, password):
    url = api_url.rstrip('/') + '/api/v1/auth/login'
    r = requests.post(url, json={'username': username, 'password': password}, timeout=10)
    r.raise_for_status()
    return r.json()['access_token']


def get_first_camera(api_url, token):
    url = api_url.rstrip('/') + '/api/v1/cameras'
    r = requests.get(url, headers={'Authorization': f'Bearer {token}'}, timeout=10)
    r.raise_for_status()
    items = r.json()
    if not items:
        raise SystemExit('No cameras found in API')
    return items[0]['id']


def post_event(api_url, token, camera_id, identifier, confidence):
    url = api_url.rstrip('/') + '/api/v1/analytics/events'
    payload = {
        'idempotency_key': f'test-{identifier}-{int(time.time())}',
        'camera_id': camera_id,
        'event_type': 'anpr',
        'entity_identifier': identifier,
        'confidence': confidence,
        'vehicle_type': 'test',
        'event_timestamp': datetime.now(timezone.utc).isoformat(),
    }
    r = requests.post(url, json=payload, headers={'Authorization': f'Bearer {token}'}, timeout=10)
    return r.status_code, r.text


async def listen_ws(api_url, token, duration=10):
    uri = api_url.replace('http://', 'ws://').replace('https://', 'wss://').rstrip('/') + f'/ws/dashboard?token={token}'
    print('Connecting to', uri)
    try:
        async with websockets.connect(uri, ping_interval=5) as ws:
            print('WS connected, listening for', duration, 'seconds')
            start = time.time()
            while time.time() - start < duration:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=duration)
                    print('WS:', msg)
                except asyncio.TimeoutError:
                    break
    except Exception as e:
        print('WS error:', e)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--api-url', required=True)
    p.add_argument('--username')
    p.add_argument('--password')
    p.add_argument('--camera-id')
    args = p.parse_args()

    if args.username and args.password:
        token = login(args.api_url, args.username, args.password)
        print('Got token (len):', len(token))
    else:
        raise SystemExit('Provide --username and --password to obtain a token')

    cam = args.camera_id or get_first_camera(args.api_url, token)
    print('Using camera id:', cam)

    tests = [
        ('GJ01XX0001', 0.92),  # exact/high-conf
        ('GJ0IXX0001', 0.92),  # near-miss high-conf
        ('GJ01XX0001', 0.60),  # low-conf should not alert
    ]

    for ident, conf in tests:
        code, text = post_event(args.api_url, token, cam, ident, conf)
        print('Posted', ident, '->', code)

    # listen for WS messages
    asyncio.run(listen_ws(args.api_url, token, duration=12))


if __name__ == '__main__':
    main()
