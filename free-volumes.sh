#!/bin/sh
#
# List the volumes attached to this instance which do not have a mount
#
lsblk -p -J -I 259 | 
python -c 'import sys; import json; print(json.dumps([dev["name"] for dev in json.loads(sys.stdin.read())["blockdevices"] if ("children" not in dev and dev["mountpoint"] is None)]))'

