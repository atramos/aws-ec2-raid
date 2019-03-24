#!/usr/bin/python3
# Usage:
#
# create-volumes.py <count> <size>
#
# Where :
#    <count> is the number of EBS volumes to be created and configured in RAID0 mode.
#    <size> is the size in GB of each volume

import requests
import boto3
import sys
import time
import subprocess
import platform
import json

try:
	num_ebs=int(sys.argv[1])
	size=int(sys.argv[2])
	print("Creating " + str(num_ebs) + " volumes of " + str(size) + "GB each.")
except:
	print("USAGE: \n Ex: script.py <count> <size>")
	sys.exit(-1)

r = requests.get("http://169.254.169.254/latest/dynamic/instance-identity/document")
response_json = r.json()
region = response_json.get('region')
availability_zone = response_json.get('availabilityZone')
instance_id = response_json.get('instanceId')

#
# set a uuid so we can easily identify related volumes in the console
# the uuid is not actually utilized by the script.
#
import uuid
raid_id = str(uuid.uuid4())

ec2 = boto3.resource('ec2',region_name=region)
client = boto3.client('ec2',region_name=region)

for x in range(num_ebs):
	response = client.create_volume(AvailabilityZone=availability_zone,Size=int(size),VolumeType='gp2', TagSpecifications=[{
            'ResourceType': 'volume',
            'Tags': [
                { 'Key': 'Name', 'Value': 'RAID-' + raid_id },
                { 'Key': 'created-by-instance', 'Value': instance_id },
            ]
	}])
	print(response['VolumeId'])
	client.get_waiter('volume_available').wait(VolumeIds=[response['VolumeId']])
	device = '/dev/sd' + chr(ord('g')+x)
	print('attaching to ' + device)
	attach = client.attach_volume( Device=device, InstanceId=instance_id, VolumeId=response['VolumeId'])
	print(attach)
