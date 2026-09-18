# Sample Video Setup

This prototype ships without embedded MP4 files (to keep the repository
small and avoid redistributing footage of uncertain licensing). To run the
full video-playback demonstration:

1. Obtain two short, legally usable traffic/CCTV-style clips. Good sources:
   - Your own recorded footage (dashcam, phone, or a static camera)
   - Royalty-free stock footage sites that explicitly allow redistribution
     (e.g. Pexels Videos, Pixabay Videos) — search "traffic junction" and
     "checkpoint" / "toll booth"
2. Save them as:
   - `data/sample/c001_traffic_junction.mp4`
   - `data/sample/c002_rto_checkpoint.mp4`
3. These paths match the `stream_reference` values used by `seed.py`. The
   `data/sample/` folder is mounted read-only into the backend container at
   `/media/sample` (see `docker-compose.yml`), and the backend serves it as
   static files at `GET /media/sample/<filename>`. The frontend resolves each
   camera's `playback_url` against the API base URL automatically — no
   further configuration is needed once the files exist at the paths above.
4. If no video files are present, the Camera Detail page will show "Playback
   failed" — this is expected and documented, not a bug.

**Important:** this is recorded/simulated footage. Nothing in this
application should be represented as a real-time RTSP or ONVIF camera
connection.
