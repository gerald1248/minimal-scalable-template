#!/usr/bin/env python

"""
Deploys new code to application and/or bastion
by toggling active and passive autoscaling groups
"""

import sys
import re
import json
from time import sleep
import doctest
import boto3
import botocore

USAGE = """
Usage: python [relative/path/to/]deploy.py
Arguments: none except --help/-h, which bring up this text
Develop:
$ virtualenv ve
$ source ve/bin/activate
$ pip install boto3
The script expects to find stack_ids.json in the working directory
"""
DATA_FILE = 'stack_ids.json'
GROUP_ID_PATTERN = '^.+-Group[12]-[A-Z0-9]+$'
ELB_ID_PATTERN = '^.+-ELB-[A-Z0-9]+$'

# API call handlers
def group_instance_count(group_id):
    """
    Test invalid group ID
    >>> group_instance_count('foo')
    -1
    """
    reg = re.compile(GROUP_ID_PATTERN)
    if not reg.match(group_id):
        return -1

    try:
        client = boto3.client('autoscaling')
        description = client.describe_auto_scaling_groups(AutoScalingGroupNames=[group_id])
    except botocore.exceptions.ClientError:
        print "Autoscaling client error: describe_auto_scaling_groups"
        sys.exit(127)

    return group_instance_count_json(description)

def group_range_instances(group_id):
    """
    Test invalid group ID
    >>> group_range_instances('foo')
    -1
    """
    reg = re.compile(GROUP_ID_PATTERN)
    if not reg.match(group_id):
        return -1

    try:
        client = boto3.client('autoscaling')
        description = client.describe_auto_scaling_groups(AutoScalingGroupNames=[group_id])
    except botocore.exceptions.ClientError:
        print "Autoscaling client error: describe_auto_scaling_groups"
        sys.exit(127)

    return group_range_instances_json(description)

def group_update(group_id, group_min, group_max, desired):
    """
    Test with invalid input
    >>> group_update('foo', 2, 1, 4)
    {}
    """
    if group_min > group_max or desired < group_min or desired > group_max:
        return {}

    try:
        client = boto3.client('autoscaling')
        response = client.update_auto_scaling_group(
            AutoScalingGroupName=group_id,
            MinSize=group_min,
            MaxSize=group_max,
            DesiredCapacity=desired)
    except botocore.exceptions.ClientError:
        print "Autoscaling client error: update_auto_scaling_group"
        sys.exit(127)

    return response

def elb_instance_count(elb_id):
    """
    Test invalid ELB ID
    >>> elb_instance_count('foo')
    -1
    """
    reg = re.compile(ELB_ID_PATTERN)
    if not reg.match(elb_id):
        return -1

    try:
        client = boto3.client('elb')
        description = client.describe_instance_health(LoadBalancerName=elb_id)
    except botocore.exceptions.ClientError:
        print "ELB client error: describe_instance_health"
        sys.exit(127)

    return elb_instance_count_json(description)

# JSON handlers
def group_instance_count_json(obj):
    """
    Test lifecycle parser
    >>> group_instance_count_json(json.loads('{ "AutoScalingGroups": [ { "Instances": [ { "LifecycleState": "InService" } ] } ] }'))
    1
    """
    if not obj['AutoScalingGroups']:
        return 0

    instances = obj['AutoScalingGroups'][0]['Instances']
    in_service = 0
    for instance in instances:
        if instance['LifecycleState'] == 'InService':
            in_service += 1
    return in_service

def group_range_instances_json(obj):
    """
    Test range parser
    >>> group_range_instances_json(json.loads('{"AutoScalingGroups": [{"MinSize": 1, "MaxSize": 4}]}'))
    (1, 4)
    """
    group = obj['AutoScalingGroups'][0]
    group_min = group['MinSize']
    group_max = group['MaxSize']
    return (group_min, group_max)

def elb_instance_count_json(obj):
    """
    Test state parser
    >>> elb_instance_count_json({"InstanceStates": [{"State": "InService"}]})
    1
    """
    states = obj['InstanceStates']
    in_service = 0
    for state in states:
        if state['State'] == 'InService':
            in_service += 1
    return in_service

def read_json(path):
    """
    Test with invalid input
    >>> read_json('/non/existent/path')
    {}
    """
    try:
        json_buffer = open(path)
        obj = json.load(json_buffer)
        json_buffer.close()
    except IOError:
        return {}
    return obj

def toggle_groups(id1, id2, elb):
    """
    Test with invalid input
    >>> toggle_groups('foo', 'foo', 'bar')
    Error: group IDs match
    False
    """
    # exit if same group given
    if id1 == id2:
        print "Error: group IDs match"
        return False

    # identify active and passive groups
    count1 = group_instance_count(id1)
    count2 = group_instance_count(id2)
    if count1 == -1 or count2 == -1:
        print "Error: invalid group ID"
        return False

    # variables
    interval = 20
    max_attempts = 30

    # exit if active/passive split not clear
    if (count1 > 0 and count2 > 0) or (count1 == 0 and count2 == 0):
        print "Error: one active and one passive group required"
        return False

    if count1 > count2:
        active_id = id1
        passive_id = id2
        active_count = count1
    else:
        active_id = id2
        passive_id = id1
        active_count = count2

    print "Active group: {}".format(active_id)
    print "Passive group: {}".format(passive_id)
    print "Activating {}".format(passive_id)

    active_range = group_range_instances(active_id)

    group_update(passive_id, active_range[0], active_range[1], active_count)

    healthy_instances = elb_instance_count(elb)
    if healthy_instances == -1:
        print "Error: invalid ELB ID"
        return False

    while healthy_instances < active_count * 2:
        max_attempts -= 1
        if max_attempts == 0:
            print "\nError: deployment timed out; resetting passive group"
            group_update(passive_id, 0, 0, 0)
            return False
        sys.stdout.write('.')
        sys.stdout.flush()
        sleep(interval)
        healthy_instances = elb_instance_count(elb)

    print "\nDeactivating {}".format(active_id)
    group_update(active_id, 0, 0, 0)

    print "Deployment successful"
    return True

if __name__ == "__main__":
    doctest.testmod()

    # don't run if help requested
    if len(sys.argv) > 1:
        for arg in sys.argv:
            if arg == "--help" or arg == "-h":
                print USAGE
                sys.exit(0)

    #fetch stack parameters
    try:
        STACK_IDS_OBJ = read_json(DATA_FILE)
    except IOError as ex:
        print "Can't open {}: {}".format(DATA_FILE, ex.strerror)
        sys.exit(127)
    except ValueError:
        print "Can't decode JSON file {}".format(DATA_FILE)
        sys.exit(127)

    try:
        ID1 = STACK_IDS_OBJ['id1']
        ID2 = STACK_IDS_OBJ['id2']
        ELB = STACK_IDS_OBJ['elb']
    except KeyError:
        print "Can't obtain IDs from {}".format(DATA_FILE)
        sys.exit(127)

    try:
        SUCCESS = toggle_groups(ID1, ID2, ELB)
    except botocore.exceptions.EndpointConnectionError:
        print "Can't connect to AWS endpoint"
        sys.exit(127)

    sys.exit(0 if SUCCESS else 127)
