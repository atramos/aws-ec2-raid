# aws-ec2-raid
Simple RAID0 (disk striping, for speed) on AWS EC2 instances. Get faster EBS for the same price as regular, slower EBS. The closest thing to a free lunch on AWS, outside of the free tier.

# Status
The status of this project is "experimental proof of concept". It works ok mostly, but the measured performance improvement
was very disappointing, and it's not clear why.

# Usage
Example: 8x 10GB RAID0 (80GB of capacity striped across 8 volumes)
```
git clone https://github.com/atramos/aws-ec2-raid 
cd aws-ec2-raid
sh install_pip3_boto3.txt
mkdir /raid0
python3 aws-ec2-raid.py 10 8 /raid0

```

# Benchmarks

On a t3.medium instance, Ubuntu Linux 18.x, an 8-way RAID0 array was found to be approximately 42% faster than a raw EBS volume.

# Troubleshooting

Issue
- botocore.exceptions.ClientError: An error occurred (UnauthorizedOperation) when calling the DescribeVolumes operation: You are not authorized to perform this operation.

Resolution
- Your AWS credentials need permissions to DescribeVolume, CreateVolume, AttachVolume, etc.

# More Info
- AWS documentation indicates 8x is the sweet-spot for performance. YMMV.
- To avoid snapshot corruption, do not perform "no reboot" snapshots.

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
