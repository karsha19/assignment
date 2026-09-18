#!/bin/sh
# Regenerates the two synthetic placeholder clips in this folder.
# Requires ffmpeg. These are NOT real footage -- see README.md in this
# folder for why, and for how to swap in real footage instead.
set -e
cd "$(dirname "$0")"

# C001 - stand-in for "Ahmedabad Traffic Junction": an intersection with
# three moving boxes (vehicles) crossing it, camera label + timestamp burned in.
ffmpeg -y -f lavfi -i "color=c=0x2b2f36:s=960x540:d=20:r=25" \
  -filter_complex "
    [0:v]drawbox=x=0:y=260:w=960:h=20:color=0x555b66@1:t=fill,
         drawbox=x=460:y=0:w=20:h=540:color=0x555b66@1:t=fill[bg];
    [bg]drawtext=text='CAM C001 -- Ahmedabad Traffic Junction (SYNTHETIC DEMO FOOTAGE)':x=20:y=20:fontsize=16:fontcolor=white:box=1:boxcolor=black@0.5:boxborderw=6[bg2];
    [bg2]drawtext=text='%{pts\:hms}':x=20:y=500:fontsize=18:fontcolor=0x22c55e:box=1:boxcolor=black@0.5:boxborderw=6[bg3];
    [bg3]drawbox=x='mod(t*80\,1000)-40':y=250:w=60:h=30:color=0xef4444:t=fill[v1];
    [v1]drawbox=x=450:y='mod(t*70\,600)-40':w=30:h=60:color=0x3b82f6:t=fill[v2];
    [v2]drawbox=x='980-mod(t*60\,1000)':y=270:w=55:h=28:color=0xf59e0b:t=fill[out]
  " -map "[out]" -c:v libx264 -pix_fmt yuv420p -t 20 -movflags +faststart \
  c001_traffic_junction.mp4

# C002 - stand-in for "RTO Checkpoint": a gate/barrier lane with one vehicle
# passing through, labeled with the plate seed.py registers as a watchlist match.
ffmpeg -y -f lavfi -i "color=c=0x23262d:s=960x540:d=20:r=25" \
  -filter_complex "
    [0:v]drawbox=x=80:y=180:w=800:h=180:color=0x33373f@1:t=fill[bg];
    [bg]drawtext=text='CAM C002 -- RTO Checkpoint (SYNTHETIC DEMO FOOTAGE)':x=20:y=20:fontsize=16:fontcolor=white:box=1:boxcolor=black@0.5:boxborderw=6[bg2];
    [bg2]drawtext=text='%{pts\:hms}':x=20:y=500:fontsize=18:fontcolor=0x22c55e:box=1:boxcolor=black@0.5:boxborderw=6[bg3];
    [bg3]drawbox=x=500:y=150:w=10:h='if(lt(mod(t\,10)\,5)\,200\,20)':color=0xf59e0b:t=fill[gate];
    [gate]drawbox=x='mod(t*90\,1100)-100':y=250:w=70:h=35:color=0xef4444:t=fill[v1];
    [v1]drawtext=text='GJ01XX0001':x='mod(t*90\,1100)-95':y=290:fontsize=12:fontcolor=white[out]
  " -map "[out]" -c:v libx264 -pix_fmt yuv420p -t 20 -movflags +faststart \
  c002_rto_checkpoint.mp4

echo "Regenerated c001_traffic_junction.mp4 and c002_rto_checkpoint.mp4"
