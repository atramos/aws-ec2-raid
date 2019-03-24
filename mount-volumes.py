#!/usr/bin/python3
#
# Setup and mount a RAID0 array
#

import requests
import boto3
import sys
import time
import subprocess
import platform
import json

volumes = json.loads(sys.stdin.read())
mountpoint=sys.argv[1]
print('Volumes: ' + str(volumes))
print('Mountpoint: ' + str(mountpoint))

r = requests.get("http://169.254.169.254/latest/dynamic/instance-identity/document")
response_json = r.json()
region = response_json.get('region')
availability_zone = response_json.get('availabilityZone')
instance_id = response_json.get('instanceId')
print('instance_id=' + instance_id)

def run_command(command):
    p = subprocess.Popen(command,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    return iter(p.stdout.readline, b'')

ec2 = boto3.resource('ec2',region_name=region)
client = boto3.client('ec2',region_name=region)

print("Creating the RAID0 Array...Please wait...")
cmd = "mdadm --create --verbose /dev/md0 --level=0 --name=MY_RAID --raid-devices=" + str(len(volumes)) + " " + " ".join(volumes)
print(cmd)
command_user = cmd.split()
subprocess.run(command_user)
time.sleep(30)

comm=('mdadm --detail --scan').split()
for line in run_command(comm):
	print(line)
	with open('/etc/mdadm/mdadm.conf', 'a') as fd:
		fd.write(line.decode('utf-8'))
		print("Creating filesystem ...")
		comm2 = ("mkfs.ext4 -L MY_RAID /dev/md0").split()
		run_command(comm2)
		time.sleep(10)
        
comm_mkdir=("mkdir -p "+ mountpoint).split()
subprocess.run(comm_mkdir)

print("Mounting " + mountpoint + " and adding to FSTAB")
comm_mount=("mount /dev/md0 " +mountpoint).split()
subprocess.run(comm_mount)


comm=("lsblk  /dev/md0 -J -o UUID").split()
r = subprocess.check_output(comm)
response_json = json.loads(r.decode('utf-8'))
md_UUID='UUID='+response_json.get('blockdevices')[0].get('uuid')

file = open('/etc/fstab','r')
found=0
for line in file:
        if md_UUID in line:
                if mountpoint in line:
                        found = 1

if found !=1:
        file2=open('/etc/fstab','a')
#        line_to_add = md_UUID +"       " + mountpoint + "       ext4     defaults,nofail 0       2\n"
        line_to_add = "LABEL=MY_RAID    " + mountpoint + "      ext4     defaults,nofail 0       2\n"
        file2.write(line_to_add)
        file2.close()

file.close()

print("Updating bootimg...")
comm=("update-initramfs -u").split()
run_command(comm)
time.sleep(5)
