On AWS execute steps:

1 Create an IAM Role and give it full EC2 access:IAM ---> Roles --->Create Role --->Aws Service - EC2 ---> Permissions: AmazonEC2FullAccess
2 Attach the role to the instance: Instance Settings ---> Attach/Replace IAM Role

In the VM execute the steps(Execute as root):

1 apt install python3-pip
2 pip3 install -r requirements.txt
3 python3 script.py 3 1 /data
