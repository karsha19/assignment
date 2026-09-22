import argparse
import time
import uuid
import json
import re
import os
import logging
from datetime import datetime, timezone

import cv2
import pytesseract
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("rtsp_ingest")

PLATE_CANDIDATE_RE = re.compile(r"[A-Z0-9]{4,}")


def extract_plate_candidates(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    scale = 800.0 / max(w, h) if max(w, h) < 1200 else 1.0
    if scale != 1.0:
        gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)

    den = cv2.bilateralFilter(gray, 9, 75, 75)
    thr = cv2.adaptiveThreshold(den, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                cv2.THRESH_BINARY, 11, 2)

    custom_oem_psm = "--oem 3 --psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    data = pytesseract.image_to_data(thr, output_type=pytesseract.Output.DICT, config=custom_oem_psm)
    texts = []
    n = len(data.get('text', []))
    for i in range(n):
        txt = data['text'][i].strip()
        conf = int(data['conf'][i]) if data['conf'][i].isdigit() else -1
        if not txt:
            continue
        norm = re.sub(r'[^A-Z0-9]', '', txt.upper())
        if len(norm) >= 4:
            texts.append((norm, conf))
    return texts


def pick_best_candidate(cands):
    if not cands:
        return None, 0.0
    cands_sorted = sorted(cands, key=lambda x: (x[1], len(x[0])), reverse=True)
    best, conf = cands_sorted[0]
    conf_f = (conf / 100.0) if conf >= 0 else 0.0
    return best, conf_f


def post_event(api_url, token, camera_id, identifier, confidence):
    url = api_url.rstrip('/') + '/api/v1/analytics/events'
    payload = {
        'idempotency_key': str(uuid.uuid4()),
        'camera_id': camera_id,
        'event_type': 'anpr',
        'entity_identifier': identifier,
        'confidence': confidence,
        'vehicle_type': 'unknown',
        'event_timestamp': datetime.now(timezone.utc).isoformat(),
    }
    headers = {
        'Content-Type': 'application/json',
    }
    if token:
        headers['Authorization'] = f'Bearer {token}'
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=10)
        if r.status_code in (200, 201):
            logger.info('Posted event %s (conf=%.2f) OK', identifier, confidence)
            return True
        else:
            logger.warning('Event post failed %s: %s %s', identifier, r.status_code, r.text)
            return False
    except Exception as e:
        logger.exception('Failed to post event: %s', e)
        return False


def run_loop(rtsp, camera_id, api_url, token, interval):
    cap = cv2.VideoCapture(rtsp)
    if not cap.isOpened():
        logger.error('Failed to open RTSP stream: %s', rtsp)
        return
    logger.info('Connected to RTSP: %s', rtsp)
    last_post = 0
    frame_count = 0
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                logger.warning('Frame read failed, reconnecting...')
                time.sleep(1)
                cap.release()
                cap = cv2.VideoCapture(rtsp)
                continue
            frame_count += 1
            now = time.time()
            if now - last_post < interval:
                time.sleep(0.01)
                continue
            last_post = now

            cands = extract_plate_candidates(frame)
            best, conf = pick_best_candidate(cands)
            if best and conf > 0.0:
                post_event(api_url, token, camera_id, best, conf)
            else:
                logger.debug('No candidate detected in frame %d', frame_count)
    finally:
        cap.release()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--rtsp', required=True)
    p.add_argument('--camera-id', required=True)
    p.add_argument('--api-url', default=os.getenv('API_URL', 'http://localhost:8000'))
    p.add_argument('--auth-token', default=os.getenv('AUTH_TOKEN'))
    p.add_argument('--interval', type=float, default=float(os.getenv('FRAME_INTERVAL', '1.0')))
    args = p.parse_args()

    run_loop(args.rtsp, args.camera_id, args.api_url, args.auth_token, args.interval)


if __name__ == '__main__':
    main()
