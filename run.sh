#!/bin/bash

# 除了alignment的 meshing 和 optimization之外，其他命令后面都可以跟--start A --stop B
echo "---------- Stitch matching ----------"
python3 scripts/stitch_main.py --mode matching
echo "---------- Stitch optimization ----------"
python3 scripts/stitch_main.py --mode optimization
echo "---------- Stitch rendering ----------"
python3 scripts/stitch_main.py --mode rendering

echo "---------- Thumbnail downsample ----------"
python3 scripts/thumbnail_main.py --mode downsample
echo "---------- Thumbnail matching ----------"
python3 scripts/thumbnail_main.py --mode match
echo "---------- Thumbnail optimization ----------"
python3 scripts/thumbnail_main.py --mode optimization
echo "---------- Thumbnail rendering ----------"
python3 scripts/thumbnail_main.py --mode render

echo "---------- Align meshing ----------"
python3 scripts/align_main.py --mode meshing
echo "---------- Align matching ----------"
python3 scripts/align_main.py --mode matching
echo "---------- Align optimization ----------"
python3 scripts/align_main.py --mode optimization
echo "---------- Align rendering ----------"
python3 scripts/align_main.py --mode rendering
