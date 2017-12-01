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


def execute():
    ec2client = boto3.client('ec2')
    ec2resource = boto3.resource('ec2')

    # instance_sgroups will contain a mapping of instances to security groups
    instance_sgroups = {}

    # sgroups_instance will contain a mapping of security groups to instances
    sgroups_instance = {}

    # all_sgroups will contain an index of all security groups associated with instances
    all_sgroups = []

    # sgroups_open_ports will contain a mapping of sgroups to open ports
    sgroups_open_ports = {}


    instances = get_instances(ec2client, CHECK_INSTANCES)
    for instance in instances:
        get_related_sgroups(instance)
        instance_sgroups.setdefault(instance.get('InstanceId'), {})
        sgroups = get_related_sgroups(instance)
        for sgroup in sgroups:
            sgroups_instance.setdefault(sgroup, [])
            sgroups_instance[sgroup].append(instance.get('InstanceId'))
        instance_sgroups[instance.get('InstanceId')] = sgroups
        [all_sgroups.append(i) for i in sgroups]
        print(instance)

    for sgroup in all_sgroups:
        open_ports = get_open_sgroups(ec2resource, sgroup)
        if open_ports:
            sgroups_open_ports.setdefault(sgroup, [])
            sgroups_open_ports[sgroup] = open_ports

    return instance_sgroups, sgroups_open_ports, sgroups_instance

if __name__ == "__main__":
    instance_sgroups, sgroups_open_ports, sgroups_instance = execute()
    # todo: the following lines have some logic issues i think
    print('The following instances have ports open to the world')
    for sg in sgroups_open_ports.keys():
        for sgroup, instance in sgroups_instance.iteritems():
            if sg == sgroup:
                i = instance.pop()
                print(i)
                print(sgroups_open_ports.get(sg))


