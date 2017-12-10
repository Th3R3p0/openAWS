import boto3

# defaults to only look at running instances. Add "stopped" to list if you want
#  to check for stopped instances as well
CHECK_INSTANCES = ["running"]


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


if __name__ == "__main__":
    ec2client = boto3.client('ec2')
    ec2resource = boto3.resource('ec2')

    aws_objects = {
      "instances": {},
      "security-groups": {}
    }

    instances = get_instances(ec2client, CHECK_INSTANCES)
    for instance in instances:
        aws_objects["instances"][instance.get('InstanceId')] = instance
        sgroups = get_related_sgroups(instance)
        for sgroup in sgroups:
            aws_objects["security-groups"][sgroup] = {}

    for sgroup in aws_objects['security-groups']:
        sgroup_info = ec2resource.SecurityGroup(sgroup)
        aws_objects['security-groups'].setdefault(sgroup, {})
        aws_objects['security-groups'][sgroup]["full_object"] = sgroup_info.ip_permissions
        ports = []
        for permission in sgroup_info.ip_permissions:
            for range in permission.get('IpRanges'):
                if range.get('CidrIp') == '0.0.0.0/0':
                    ports.append(permission.get('FromPort'))
        aws_objects['security-groups'][sgroup]["open_ports"] = ports

    for instanceid, object in aws_objects.get("instances").iteritems():
        open_ports = []
        for sg in object['SecurityGroups']:
            if aws_objects['security-groups'][sg.get('GroupId')]['open_ports']:
                for i in aws_objects['security-groups'][sg.get('GroupId')]['open_ports']:
                    if i == 0:
                        i = "*"
                    open_ports.append(i)
        if open_ports:
            print("=====================")
            print("Instance ID: {}".format(instanceid))
            if object.get('Tags'):
                for i in object.get('Tags'):
                    if i.get('Key') == 'Name':
                        print("Name: {}".format(i.get('Value')))
            if object.get('PublicIpAddress'):
                print("Public IP: {}".format(object.get('PublicIpAddress')))
            print("Open Ports: {}".format(open_ports))
