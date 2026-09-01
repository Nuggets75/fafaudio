#!/bin/bash
set -e

Xvfb :99 -screen 0 800x600x24 &
sleep 1

if [ ! -f /wine/system.reg ]; then
    echo "First run: initialising wine prefix at /wine..."
    wineboot --init
    wineserver -w
    echo "Wine prefix initialised."
fi

if [ ! -f /wine/.dxsdk-installed ]; then
    echo "First run: installing XACT binaries from /xact-binaries..."
    /setup/install-dxsdk.sh || {
        echo "XACT install FAILED. Container will still start so you can debug."
        echo "See README.md for troubleshooting."
    }
fi

if [ ! -f "/wine/drive_c/xact/XactBld3.exe" ] && [ ! -f "/wine/drive_c/xact/XactBld.exe" ]; then
    echo "WARNING: no XactBld found under /wine/drive_c/xact/"
    echo "The web UI will start, but builds will fail until you fix this."
fi

echo "Starting Flask server on :5000..."
exec gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 120 server:app
