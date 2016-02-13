#!/usr/bin/env python

"""
Deploys new code
by toggling active and passive autoscaling groups
"""

import sys
import json
from time import sleep
import doctest
import boto3

# API call handlers
def group_instance_count(group_id):
    client = boto3.client('autoscaling')
    description = client.describe_auto_scaling_groups(AutoScalingGroupNames=[group_id])
    return group_instance_count_json(description)

def group_range_instances(group_id):
    client = boto3.client('autoscaling')
    description = client.describe_auto_scaling_groups(AutoScalingGroupNames=[group_id])
    return group_range_instances_json(description)

def group_update(group_id, group_min, group_max, desired):
    client = boto3.client('autoscaling')
    response = client.update_auto_scaling_group(
        AutoScalingGroupName=group_id,
        MinSize=group_min,
        MaxSize=group_max,
        DesiredCapacity=desired)
    return response

def elb_instance_count(elb_id):
    client = boto3.client('elb')
    description = client.describe_instance_health(LoadBalancerName=elb_id)
    return elb_instance_count_json(description)

# JSON handlers
def group_instance_count_json(obj):
    """
    Test lifecycle parser
    >>> group_instance_count_json(json.loads('{ "AutoScalingGroups": [ { "Instances": [ { "LifecycleState": "InService" } ] } ] }'))
    1
    """
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
    json_buffer = open(path)
    obj = json.load(json_buffer)
    json_buffer.close()
    return obj

def toggle_groups(id1, id2, elb):
    # identify active and passive groups
    count1 = group_instance_count(ID1)
    count2 = group_instance_count(ID2)

    # variables
    interval = 90
    max_attempts = 10

    # exit if active/passive split not clear
    if (count1 > 0 and count2 > 0) or (count1 == 0 and count2 == 0):
        print "Error: one active and one passive group required"
        sys.exit(1)

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
    while healthy_instances < active_count * 2:
        max_attempts -= 1
        if max_attempts == 0:
            print "Error: deployment timed out; resetting passive group"
            group_update(passive_id, 0, 0, 0)
            sys.exit(2)
        sleep(interval)
        healthy_instances = elb_instance_count(elb)

    print "Deactivating {}".format(active_id)
    group_update(active_id, 0, 0, 0)

    print "Deployment successful"

if __name__ == "__main__":
    doctest.testmod()

    # don't run if help requested
    if len(sys.argv) > 1:
        for arg in sys.argv:
            if arg == "--help" or arg == "-h":
                print "Ensure stack_ids.json is present in the working directory"
                sys.exit(0)

    #fetch stack-specific parameters
    STACK_IDS_OBJ = read_json('stack_ids.json')
    ID1 = STACK_IDS_OBJ['id1']
    ID2 = STACK_IDS_OBJ['id2']
    ELB = STACK_IDS_OBJ['elb']

    toggle_groups(ID1, ID2, ELB)
    sys.exit(0)

