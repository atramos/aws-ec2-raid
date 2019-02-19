# Usage:
#
# aws-ec2-raid.py <count> <size> <mountpoint>
#
# Where :
#    <count> is the number of EBS volumes to be created and configured in RAID0 mode.
#    <size> is the size in GB of each volume
#    <mountpoint> is the path for the mount in the local fs, e.g. /mnt or /data

import requests
import boto3
import sys
import time
import subprocess


if len(sys.argv) == 4:
	num_ebs=sys.argv[1]
	size=sys.argv[2]
	mountpoint=sys.argv[3]
else:
	print("Not playing fair: \n Ex: script.py <count> <size> <mountpoint>")
	sys.exit(0)

def run_command(command):
    p = subprocess.Popen(command,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    return iter(p.stdout.readline, b'')


r = requests.get("http://169.254.169.254/latest/dynamic/instance-identity/document")
response_json = r.json()
region = response_json.get('region')
availability_zone = response_json.get('availabilityZone')
instance_id = response_json.get('instanceId')


ec2 = boto3.resource('ec2',region_name=region)
client = boto3.client('ec2',region_name=region)

volumes = ec2.volumes.all()

  
num_free=0
for vol in volumes:
	if (vol.state == 'available' or vol.state == 'creating') and str(vol.size) == str(size):
		num_free+=1

if num_free >= int(num_ebs):
	print("Number of free volumes is equal to number of created ebs")
	num = 0
#	break
else: 
	print("Verifying if raid array already exists. There may be one array only!")
	#Create needed 
	num = int(num_ebs) - num_free
	try:
		comm2 = ("mdadm --detail /dev/md0").split()
		subprocess.check_output(comm2,stderr=subprocess.STDOUT)
		#print('raid array exists Hurray')
		#sys.exit(0)
		existing_md=1
	except subprocess.CalledProcessError as e:
		#sys.exit(0)
		existing_md=0
		for x in range(num):
			response = client.create_volume(AvailabilityZone=availability_zone,Size=int(size))
		time.sleep(30)

j=0

alphabet='bcdefghijklmopqrstuvwxyz'
all_devices=""
for vol in volumes:
	if vol.state == 'in-use':
		continue
	if vol.state == 'available' and str(vol.size) == str(size):
		if j < int(num_ebs):
			print("Attaching volume with id " + vol.id + " to instance: "+ instance_id)
			response = client.attach_volume(
    				Device='/dev/sd'+alphabet[j],
    				InstanceId=instance_id,
    				VolumeId=vol.id
				)
			all_devices=all_devices+'/dev/sd'+alphabet[j]+" "
		j+=1
	elif vol.state == 'creating':
		print("Some of the volumes are creating, you should wait a bit and restart this")

#sudo mdadm --create --verbose /dev/md0 --level=0 --name=MY_RAID --raid-devices=number_of_volumes device_name1 device_name2
time.sleep(30)
if existing_md == 0:
	print("Creating the RAID0 Array...Please wait...")
	command_user = ("mdadm --create --verbose /dev/md0 --level=0 --name=MY_RAID --raid-devices=" + num_ebs + " " + all_devices).split()
	subprocess.run(command_user)
	time.sleep(30)
	print("Creating filesystem of type XFS...")
	try:
		comm2 = ("mkfs -t xfs -f /dev/md0").split()
		subprocess.check_output(comm2,stderr=subprocess.STDOUT)
	except subprocess.CalledProcessError as e:
		print("There is an error with formatting the volume")
	
comm=('mdadm --detail --scan').split()
for line in run_command(comm):
        with open('/etc/mdadm.conf', 'w') as fd:
                fd.write(line.decode('utf-8'))

comm_mkdir=("mkdir -p "+ mountpoint).split()
subprocess.run(comm_mkdir)

print("Mounting " + mountpoint + " and adding to FSTAB")
comm_mount=("mount /dev/md0 " +mountpoint).split()
subprocess.run(comm_mount)

file = open('/etc/fstab','r')
found=0
for line in file:
	if "md0" in line:
		if mountpoint in line:
			found = 1

if found !=1:
        file2=open('/etc/fstab','a')
        line_to_add = "/dev/md0	" + mountpoint + "       xfs     defaults,nofail 0       2\n"
        file2.write(line_to_add)
        file2.close()

file.close()
