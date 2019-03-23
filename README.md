# aws-ec2-raid
Simple RAID0 (disk striping, for speed) on AWS EC2 instances. Get faster EBS for the same price as regular, slower EBS. The closest thing to a free lunch on AWS, outside of the free tier.

# Status
The status of this project is "unstable proof of concept". It worked fine once, but it breaks easily depending on what else
is present in the environment. The attachment order of NVMe devices on boot is not guaranteed by AWS, and that really messes things up.

# Usage
Example: 8x 10GB RAID0 (80GB of capacity striped across 8 volumes)
```
git clone https://github.com/atramos/aws-ec2-raid 
cd aws-ec2-raid/aws-ec2-raid
sh install_pip3_boto3.txt
mkdir /raid0
python3 aws-ec2-raid.py 10 8 /raid0

```

# Benchmarks
All tests executed on a t3.medium instance, Ubuntu Linux 18.x with PostgreSQL 10.5 where applicable.

TBD

# Troubleshooting

Issue
- botocore.exceptions.ClientError: An error occurred (UnauthorizedOperation) when calling the DescribeVolumes operation: You are not authorized to perform this operation.

Resolution
- Your AWS credentials need permissions to DescribeVolume, CreateVolume, AttachVolume, etc.

# More Info
- AWS documentation indicates 8x is the sweet-spot for performance. YMMV.
- To avoid snapshot corruption, do not perform "no reboot" snapshots.
