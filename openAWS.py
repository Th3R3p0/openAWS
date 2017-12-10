import boto3
import argparse
import json

# defaults to only look at running instances. Add "stopped" to list if you want
#  to check for stopped instances as well
CHECK_INSTANCES = ["running"]
VERBOSITY = False


ALL_REGIONS = ["us-east-1", "us-east-2", "us-west-1", "us-west-2", "ap-south-1", "ap-northeast-1", "ap-northeast-2",
               "ap-southeast-1", "ap-southeast-2", "ca-central-1", "eu-central-1", "eu-west-1", "eu-west-2",
               "sa-east-1"]


# this function returns a list of instance objects based on a state filter
def get_instances(ec2client, filter):
    instances = []
    ec2_response = ec2client.describe_instances()
    for reservation in ec2_response.get("Reservations"):
        for instance in reservation.get("Instances"):
            if instance.get('State').get('Name') in filter:
                instances.append(instance)
    return instances


# this function will return a list of security groups associated with an instance
def get_related_sgroups(instance):
    sgroups = []
    for sgroup in instance.get('SecurityGroups'):
        group_id = sgroup.get('GroupId')
        sgroups.append(group_id)
    return sgroups


# this function looks through a security group for any 0.0.0.0/0 on a specific port and
#   returns a list of ports for which are publicly available
def get_open_sgroups(ec2resource, sgroup):
    ports = []
    sg_details = ec2resource.SecurityGroup(sgroup)
    for permission in sg_details.ip_permissions:
        for range in permission.get('IpRanges'):
            if range.get('CidrIp') == '0.0.0.0/0':
                ports.append(permission.get('FromPort'))
    return ports


def populate_aws_objects(ec2client, ec2resource, region):
    instances = get_instances(ec2client, CHECK_INSTANCES)
    for instance in instances:
        AWS_OBJECTS[region]["instances"][instance.get('InstanceId')] = instance
        sgroups = get_related_sgroups(instance)
        for sgroup in sgroups:
            AWS_OBJECTS[region]["security-groups"][sgroup] = {}

    for sgroup in AWS_OBJECTS[region]['security-groups']:
        sgroup_info = ec2resource.SecurityGroup(sgroup)
        AWS_OBJECTS[region]['security-groups'].setdefault(sgroup, {})
        AWS_OBJECTS[region]['security-groups'][sgroup]["full_object"] = sgroup_info.ip_permissions
        ports = []
        for permission in sgroup_info.ip_permissions:
            for range in permission.get('IpRanges'):
                if range.get('CidrIp') == '0.0.0.0/0':
                    ports.append(permission.get('FromPort'))
        AWS_OBJECTS[region]['security-groups'][sgroup]["open_ports"] = ports


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='A tool to list open ports to your EC2 instances based on your'
                                                 'security groups.')
    parser.add_argument('--region', help='Specify a specific region. If not set, region from AWS config will be used.'
                                         'You can also specify multiple regions', nargs="*")
    parser.add_argument('--all-regions', help='Set to True, if you want to run in all regions', type=bool)
    parser.add_argument('--verbose', help="Set this to True, if you want verbose otuput", type=bool)
    parser.add_argument('--out-file', help="Outputs instances with open ports to file in dictionary format", type=str)
    args = parser.parse_args()
    if args.region and args.all_regions:
        raise ValueError("You cannot specify `region` and `all-regions` at the same time.")
    elif args.region:
        regions = [args.region]
    elif args.all_regions:
        regions = ALL_REGIONS
    else:
        regions = [boto3.session.Session().region_name]
    if args.verbose == True:
        VERBOSITY = True

    AWS_OBJECTS = {}

    for region in regions:
        AWS_OBJECTS[region] = {
                                "instances": {},
                                "security-groups": {}
                                }

        ec2client = boto3.client('ec2', region_name=region)
        ec2resource = boto3.resource('ec2', region_name=region)
        if VERBOSITY:
            print("Fetching data for {}".format(region))

        populate_aws_objects(ec2client, ec2resource, region)

    open_hosts = {}
    for region, objects in AWS_OBJECTS.iteritems():
        open_hosts[region] = {}
        print("========================")
        print("Region: {}".format(region))
        for instanceid, object in objects['instances'].iteritems():
            open_ports = []
            for sg in object['SecurityGroups']:
                if AWS_OBJECTS[region]['security-groups'][sg.get('GroupId')]['open_ports']:
                    for i in AWS_OBJECTS[region]['security-groups'][sg.get('GroupId')]['open_ports']:
                        if i == 0:
                            i = "*"
                        open_ports.append(i)
            if open_ports:
                open_hosts[region][instanceid] = {
                    "IP": object.get('PublicIpAddress'),
                    "Open-Ports": open_ports,
                }
                print("-------------------")
                print("Instance ID: {}".format(instanceid))
                if object.get('Tags'):
                    for i in object.get('Tags'):
                        if i.get('Key') == 'Name':
                            open_hosts[region][instanceid]["Instance-Name"] = i.get('Value')
                            print("Name: {}".format(i.get('Value')))
                else:
                    open_hosts[region][instanceid]["Instance-Name"] = None
                if object.get('PublicIpAddress'):
                    print("Public IP: {}".format(object.get('PublicIpAddress')))
                print("Open Ports: {}".format(open_ports))
    if args.out_file:
        with open(args.out_file, 'w') as f:
            f.writelines(json.dumps(open_hosts))
