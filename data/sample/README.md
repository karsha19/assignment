# Sample Video

This folder ships with two working sample video files:

- `c001_traffic_junction.mp4` — stand-in for Camera C001 (Ahmedabad Traffic Junction)
- `c002_rto_checkpoint.mp4` — stand-in for Camera C002 (RTO Checkpoint), showing
  the exact plate (`GJ01XX0001`) that `seed.py` registers as a watchlist match,
  so the video, the seeded detection events, and the alert demo all line up

**These are synthetically generated placeholder clips (built with ffmpeg —
moving colored boxes standing in for vehicles, burned-in camera label and
timestamp), not real CCTV footage.** They exist so the recorded-video
playback pipeline (static serving, HTML5 `<video>`, error states) is fully
exercised out of the box without redistributing footage of uncertain
licensing. Each clip is clearly labeled on-frame as synthetic, and the app
labels the source protocol as "recorded" everywhere in the UI — nothing here
is presented as a live or real camera feed.

They are wired up by default: `seed.py` sets each camera's
`stream_reference` to `/media/sample/<filename>`, the backend serves this
folder as static files at `GET /media/sample/<filename>` (see
`app/main.py`), and the frontend resolves each camera's `playback_url`
against the API base URL automatically. No extra configuration is needed —
`docker compose up --build` (or a local `alembic upgrade head && python
seed.py`) gives you working video playback immediately.

## Swapping in real footage for your final submission

If you'd rather use real, legally usable footage for the actual submission
(recommended for the video-demonstration deliverable, since the assignment
asks for "legally usable sample CCTV footage or self-created recorded
footage"):

1. Obtain two short clips — your own recording, or footage from a
   stock-video site that explicitly allows redistribution (e.g. Pexels
   Videos, Pixabay Videos); search "traffic junction" / "checkpoint" or
   "toll booth".
2. Replace `c001_traffic_junction.mp4` and `c002_rto_checkpoint.mp4` with
   your files (same filenames, or update `stream_reference` on each camera
   from the Camera Registry UI if you rename them).
3. Everything else — static serving, playback, error handling — keeps
   working unchanged.

## Regenerating the placeholder clips

The exact ffmpeg commands used to generate the two included clips are in
`data/sample/generate_placeholder_videos.sh` if you want to tweak duration,
resolution, or the on-screen labels.
