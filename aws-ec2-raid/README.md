#Automated EBS RAID0 setup on EC2 Linux 

This script automated this process: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/raid-config.html

#Usage

```
aws-ec2-raid.py <count> <size> <mountpoint>
```
Where :
<count> is the number of EBS volumes to be created and configured in RAID0 mode.
<size> is the size in GB of each volume
<mountpoint> is the path for the mount in the local fs, e.g. /mnt or /data

Example:
```
setup_raid.py 10 2 /data
```
This will create 10 EBS volumes of 2GB each, format them using mdadm, and mount then in /data.

Detailed requirements:
- The script will be run on the machine where the mount is desired.
- The script will create the EBS volumes.
- The script will run the mdadm commands as described in the linked documentation.
- The script will format the volume
- The script will mount the volume
- The script will update /etc/fstab so that the volume persists on reboot

#Deployment

On AWS execute steps:

1 Create an IAM Role and give it full EC2 access:IAM ---> Roles --->Create Role --->Aws Service - EC2 ---> Permissions: AmazonEC2FullAccess
2 Attach the role to the instance: Instance Settings ---> Attach/Replace IAM Role

In the VM execute the steps(Execute as root):

1 apt install python3-pip
2 pip3 install -r requirements.txt
3 python3 script.py 3 1 /data

#Future Enhancements

- RAID10 would be nice