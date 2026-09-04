#!/bin/bash
# One-time DirectX SDK installer.
# Copies XACT binaries from a host-mounted read-only volume at /xact-binaries
# into the persistent wine prefix at /wine/drive_c/xact.
#
# You (the user) provide these binaries by mounting a host folder containing
# them at /xact-binaries in the container. See README.md.

set -e

SRC=/xact-binaries
DST=/wine/drive_c/xact

if [ ! -d "$SRC" ]; then
    echo "ERROR: $SRC does not exist inside container."
    echo "Mount your XACT binaries folder to /xact-binaries (see README.md)."
    exit 1
fi

if [ -z "$(ls -A "$SRC" 2>/dev/null)" ]; then
    echo "ERROR: $SRC is empty."
    echo "Copy your XACT binaries into the host folder that maps to /xact-binaries."
    exit 1
fi

mkdir -p "$DST"
cp -r "$SRC"/* "$DST"/

if [ ! -f "$DST/XactBld3.exe" ] && [ ! -f "$DST/XactBld.exe" ]; then
    echo "ERROR: neither XactBld3.exe nor XactBld.exe found in $DST"
    echo "Contents of $DST:"
    ls -la "$DST"
    exit 1
fi

touch /wine/.dxsdk-installed
echo "XACT binaries installed to $DST"
