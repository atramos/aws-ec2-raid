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
import platform
import json

r = requests.get("http://169.254.169.254/latest/dynamic/instance-identity/document")
response_json = r.json()
region = response_json.get('region')
availability_zone = response_json.get('availabilityZone')
instance_id = response_json.get('instanceId')

def run_command(command):
    p = subprocess.Popen(command,
                         stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT)
    return iter(p.stdout.readline, b'')

def delete_entry(path,entry):
  data=""
  with open(path,"r") as f:
    lines = f.readlines()
    for line in lines:
      if entry in line:
        print("Deleting " + path + " entry...")
      else:
        data+=line
  with open(path, "w") as f:
    f.write(data)


if len(sys.argv) == 2:
	if sys.argv[1] == "--cleanup":
		ec2 = boto3.resource('ec2',region_name=region)
		client = boto3.client('ec2',region_name=region)
		print("Will cleanup any attached volumes")
		try:
			comm2 = ("umount LABEL=MY_RAID").split()
			run_command(comm2)
		except subprocess.CalledProcessError as e:
			print('Nothing to umount')
		try:
			comm2 = ("mdadm --detail --stop --scan /dev/md0 -q").split()
			run_command(comm2)
			time.sleep(5)
		except subprocess.CalledProcessError as e:
			print('Nothing to stop' + str(e))
		comm2 = ("touch /opt/.volumes").split()
		subprocess.check_output(comm2,stderr=subprocess.STDOUT)
		file = open('/opt/.volumes','r')
		for line in file:
			if line !="":
				response = client.detach_volume(VolumeId=line)
		file.close()
		file = open('/opt/.volumes','r')
		for line in file:
			print("Waiting detaching of volume with id " + line)
			client.get_waiter('volume_available').wait(VolumeIds=[line])
			print("Deleting volume with id " + line)
			response = client.delete_volume(VolumeId=line)
		file.close()
		f = open("/opt/.volumes",'w')
		f.close()
		comm2 = ("mdadm --detail --stop --scan /dev/md0 -q").split()
		run_command(comm2)
		delete_entry("/etc/fstab","LABEL=MY_RAID")
		delete_entry("/etc/mdadm/mdadm.conf","/dev/md0")	
		sys.exit(0)
	else:
		print("Not playing fair: \n Only --cleanup is available")
		sys.exit(0)

if len(sys.argv) == 4:
	num_ebs=sys.argv[1]
	size=sys.argv[2]
	mountpoint=sys.argv[3]
else:
	print("Not playing fair: \n Ex: script.py <count> <size> <mountpoint>")
	sys.exit(0)

def linux_distribution():
  try:
    return platform.linux_distribution()
  except:
    return "N/A"


for line in linux_distribution():
	if line == 'Ubuntu':
		platform='ubuntu'
	
if platform != 'ubuntu' :
	platform = 'amazon'



ec2 = boto3.resource('ec2',region_name=region)
client = boto3.client('ec2',region_name=region)

volumes = ec2.volumes.all()

  
num_free=0
for vol in volumes:
	if (vol.state == 'available' or vol.state == 'creating') and str(vol.size) == str(size):
		num_free+=1

existing_md = 0
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
		print('raid array exists Hurray')
		sys.exit(0)
		existing_md = 1
	except subprocess.CalledProcessError as e:
		print('raid array not found')
		for x in range(num):
			response = client.create_volume(AvailabilityZone=availability_zone,Size=int(size),VolumeType='gp2')
		time.sleep(30)
		existing_md = 0

j=0

alphabet='bcdefghijklmopqrstuvwxyz'
if platform == 'ubuntu':
	dev = '/dev/xvd'
	ssd_type='ssd'
else:
	dev = '/dev/sd'
	ssd_type='ssd'

comm=('parted --list').split()
for line in run_command(comm):
        if "Model: NVMe Device" in str(line):
                ssd_type='nvme'


all_devices=""
for vol in volumes:
	if vol.state == 'in-use':
		continue
	if vol.state == 'available' and str(vol.size) == str(size):
		if j < int(num_ebs):
			print("Attaching volume with id " + vol.id + " to instance: "+ instance_id)
			file = open('/opt/.volumes','a')
			file.write(vol.id + "\n")
			file.close()
				
			response = client.attach_volume(
    				Device=dev+alphabet[j],
    				InstanceId=instance_id,
    				VolumeId=vol.id
				)

			response = client.modify_instance_attribute(
				Attribute='blockDeviceMapping',
				BlockDeviceMappings=[
				{
					'DeviceName': dev+alphabet[j],
					'Ebs': {
						'DeleteOnTermination': True,
						'VolumeId': vol.id
					},
				},
				],
				InstanceId=instance_id
				)
			if ssd_type=='ssd':
				all_devices=all_devices+ dev +alphabet[j]+" "
			else:
				if j > 8:
					all_devices=all_devices+"/dev/nvme"+str(int((j+1)/10))+str(int((j+1)%10))+"n1"+" "
				else:
					all_devices=all_devices+"/dev/nvme"+ str(j+1)+"n1"+" "
		j+=1
	elif vol.state == 'creating':
		print("Some of the volumes are creating, you should wait a bit and restart this")

time.sleep(30)

if existing_md == 0:
	print("Creating the RAID0 Array...Please wait...")
	command_user = ("mdadm --create --verbose /dev/md0 --level=0 --name=MY_RAID --raid-devices=" + num_ebs + " " + all_devices).split()
	subprocess.run(command_user)
	time.sleep(30)

	comm=('mdadm --detail --scan').split()
	for line in run_command(comm):
		with open('/etc/mdadm/mdadm.conf', 'a') as fd:
			fd.write(line.decode('utf-8'))
			print("Creating filesystem of type XFS...")
#			comm2 = ("mkfs -t xfs -f /dev/disk/by-id/md-uuid-"+(line.split()[3].split(b'=')[1]).decode('utf-8')+":MY_RAID").split()
			comm2 = ("mkfs.xfs -L MY_RAID -f /dev/md0").split()
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
#        line_to_add = md_UUID +"	" + mountpoint + "       xfs     defaults,nofail 0       2\n"
        line_to_add = "LABEL=MY_RAID	" + mountpoint + "	xfs	defaults,nofail	0	2\n"
        file2.write(line_to_add)
        file2.close()

file.close()

print("Updating bootimg...")
comm=("update-initramfs -u").split()
run_command(comm)
time.sleep(5)
