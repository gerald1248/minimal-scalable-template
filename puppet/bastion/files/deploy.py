#!/usr/bin/env python

"""
Deploys new code
by toggling active and passive autoscaling groups
"""

import os, sys, re, json, boto3
from time import sleep

# API call handlers
def group_instance_count(id):
  client = boto3.client('autoscaling')
  description = client.describe_auto_scaling_groups(AutoScalingGroupNames=[id])
  return group_instance_count_json(description)

def group_range_instances(id):
  client = boto3.client('autoscaling')
  description = client.describe_auto_scaling_groups(AutoScalingGroupNames=[id])
  return group_range_instances_json(description)

def group_update(id, min, max, desired):
  client = boto3.client('autoscaling')
  response = client.update_auto_scaling_group(
    AutoScalingGroupName=id,
    MinSize=min,
    MaxSize=max,
    DesiredCapacity=desired)
  return 0

def elb_instance_count(id):
  client = boto3.client('elb')
  description = client.describe_instance_health(LoadBalancerName=id)
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
  min = group['MinSize']
  max = group['MaxSize']
  return (min, max)

def elb_instance_count_json(obj):
  """
  Test state parser
  >>> elb_instance_count_json({"InstanceStates": [{"State": "InService"}]})
  1
  """
  states = obj['InstanceStates'];
  in_service = 0
  for state in states:
    if state['State'] == 'InService':
      in_service += 1
  return in_service

def read_json(path):
  buffer = open(path)
  obj = json.load(buffer)
  buffer.close()
  return obj

if __name__ == "__main__":
  import doctest
  doctest.testmod();

  # don't run if help requested
  if len(sys.argv) > 1:
    for arg in sys.argv:
      if (arg == "--help" or arg == "-h"):
        print sys.argv[0] + " requires no parameters"
        sys.exit(0)

  #fetch stack-specific parameters
  stack_ids_obj = read_json('stack_ids.json')
  id1 = stack_ids_obj['id1']
  id2 = stack_ids_obj['id2']
  elb = stack_ids_obj['elb']

  # identify active and passive groups
  count1 = group_instance_count(id1)
  count2 = group_instance_count(id2)

  # variables
  interval = 90
  max_attempts = 10

  # exit if active/passive split not clear
  if ((count1 > 0 and count2 > 0) or (count1 == 0 and count2 == 0)):
    print sys.argv[0] + " requires one active and one passive group to run"
    sys.exit(1)

  if (count1 > count2):
    active_id = id1
    passive_id = id2
    active_count = count1
  else:
    active_id = id2
    passive_id = id1
    active_count = count2

  active_range = group_range_instances(active_id);

  group_update(passive_id, active_range[0], active_range[1], active_count) 

  healthy_instances = elb_instance_count(elb)
  while healthy_instances < active_count * 2:
    max_attempts -= 1
    if max_attempts == 0:
      print sys.argv[0] + " timed out"
      group_update(passive_id, 0, 0, 0)
      sys.exit(2)
    sleep(interval)
    healthy_instances = elb_instance_count(elb)

  group_update(active_id, 0, 0, 0)
  print sys.argv[0] + " successful"
  sys.exit(0)
