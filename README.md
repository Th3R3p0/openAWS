# openAWS

This script identifies any security groups that are open to the world (0.0.0.0/0).

By default it only checks security groups attached to running instances. The documentation on how to change this is in the comments in the script

## Prerequisites
```
pip install -r requirements.txt
```
* Ensure you have setup AWS config in `~/.aws/config` and `~/.aws/credentials`
    * See [AWS Documentation](http://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html)
    * IAM Policy Requirements: This tool only needs to read your Security Groups and EC2 instances. You can create a new policy for this or use the already existing `SecurityAudit` policy. This will grant a little more than needed, but only read-only access to your AWS account. See the bottom of readme for an example policy that uses the least amount of privileges.
## To run
```
python openAWS.py
```

## To do
* take command line parameters
* implement in Lambda
    * Keep a dictionary of SGs and Instances attached to the SGs in S3 of known SGs open to the world
    * Do a deepdiff to the new dictionary on lambda execution.
    * If new SGs are found, send an alert to admin
    * If instances are assigned a new SG that is more open then previously, send an alert to admin
* Output to a file so you can run an nmap scan based the output of the file

## Least Privilege IAM Policy
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "VisualEditor0",
            "Effect": "Allow",
            "Action": [
                "ec2:DescribeSecurityGroups",
                "ec2:DescribeInstanceStatus",
                "ec2:DescribeInstances"
            ],
            "Resource": "*"
        }
    ]
}
```
