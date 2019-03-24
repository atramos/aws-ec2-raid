# aws-ec2-raid
Simple RAID0 (disk striping, for speed) on AWS EC2 instances. Get faster EBS for the same price as regular, slower EBS. The closest thing to a free lunch on AWS, outside of the free tier. Inspired by AWS documentation: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/raid-config.html

# Status
The status of this project is "failed proof of concept". It works ok, but the measured performance improvement
was very disappointing, and it's not clear why. 

# Usage
```
./create-volumes.py COUNT SIZE 
./free-volumes.sh | ./mount-volumes MOUNTPOINT
```
Where :
COUNT is the number of EBS volumes to be created and configured in RAID0 mode.
SIZE is the size in GB of each volume
MOUNTPOINT is the path for the mount in the local fs, e.g. /mnt or /data

Example:

8x 10GB RAID0 (80GB of capacity striped across 8 volumes)
```
git clone https://github.com/atramos/aws-ec2-raid 
cd aws-ec2-raid
sh install_pip3_boto3.txt
mkdir /raid0
./create-volumes.py 10 8
./free-volumes.sh | ./mount-volumes /mnt
```

# Benchmarks

- Test executed on a t3.medium instance, Ubuntu Linux 18.x
- 8-way RAID0 array 
- Test procedure: ```tar -cf - . > /dev/null``` on a directory containing 43GB of data files
- RESULT: raid0 was approximately 42% faster than a raw EBS volume

# Troubleshooting

## Issue
- botocore.exceptions.ClientError: An error occurred (UnauthorizedOperation) when calling the DescribeVolumes operation: You are not authorized to perform this operation.

## Resolution
- Your AWS credentials need permissions to DescribeVolume, CreateVolume, AttachVolume, etc.
1 Create an IAM Role and give it full EC2 access:IAM ---> Roles --->Create Role --->Aws Service - EC2 ---> Permissions: AmazonEC2FullAccess
2 Attach the role to the instance: Instance Settings ---> Attach/Replace IAM Role

# How does it work?

- The script runs on the machine where the mount is desired.
- The script creates the EBS volumes using boto3 API.
- The script runs the mdadm commands as described in the AWS documentation.
- The script formats the volume
- The script mounts the volume
- The script updates /etc/fstab so that the volume persists on reboot

# Future Enhancements

- RAID10? There are online rumours that say EBS is unreliable. If true, it would be good to mirror the RAID0.
- More testing: AWS documentation indicates 8x is the sweet-spot for performance. This is the only setup I tested, and it was unimpressive.
- More testing: I have not tested this, but, to avoid snapshot corruption, you should probably not perform "no reboot" EBS snapshots.

