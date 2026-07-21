import boto3
from moto import mock_aws
from collections import Counter, defaultdict

@mock_aws
def main():
    ec2 = boto3.client("ec2", region_name="us-east-1")

    # create two fake instances
    ec2.run_instances(ImageId="ami-1", MinCount=1, MaxCount=1, InstanceType="t2.micro", TagSpecifications=[{"ResourceType": "instance", "Tags": [{"Key": "Environment", "Value": "prod"}]}])                                         
    ec2.run_instances(ImageId="ami-1", MinCount=1, MaxCount=1, InstanceType="m5.large", TagSpecifications=[{"ResourceType": "instance", "Tags": [{"Key": "Environment", "Value": "prod"}]}])                                         
    ec2.run_instances(ImageId="ami-1", MinCount=1, MaxCount=1, InstanceType="t3.small", TagSpecifications=[{"ResourceType": "instance", "Tags": [{"Key": "Environment", "Value": "dev"}]}])    
    ec2.run_instances(ImageId="ami-1", MinCount=1, MaxCount=1,InstanceType="t2.nano")      
    
    
    # ask AWS to list them
    resp = ec2.describe_instances()
    for reservation in resp["Reservations"]:
        for inst in reservation["Instances"]:
            print(inst["InstanceId"], inst["InstanceType"], tag_to_dict(inst))
    print(count_by_type(resp))
    print("unique:", unique_types(resp))
    print("groups:")
    for itype, ids in group_by_type(resp).items():
        print(f"  {itype} ({len(ids)}): {ids}")
    print("UNTAGGED:", untagged(resp))
    print("PROD:", with_tag(resp, "Environment", "prod"))
    print("by env:")
    for env, ids in group_by_env(resp).items():
        print(f"  {env} ({len(ids)}): {ids}")

def group_by_type(resp):
    groups = defaultdict(list)
    for r in resp["Reservations"]:
        for inst in r["Instances"]:
            groups[inst["InstanceType"]].append(inst["InstanceId"])
    return groups

def count_by_type(resp):
    counts = Counter()
    for r in resp["Reservations"]:
        for inst in r["Instances"]:
            counts[inst["InstanceType"]] += 1
    return counts

def unique_types(resp):
    types = set()
    for r in resp["Reservations"]:
        for inst in r["Instances"]:
            types.add(inst["InstanceType"])
    return types

def tag_to_dict(inst):
    return {t["Key"]: t["Value"] for t in inst.get("Tags", [])}

def untagged(resp):
    notags = []
    for u in resp["Reservations"]:
        for inst in u["Instances"]:
            if not inst.get("Tags"):
                notags.append((inst["InstanceId"], inst["InstanceType"]))
    return notags

def with_tag(resp, key, value):
    wtags = []
    for w in resp["Reservations"]:
        for inst in w["Instances"]:
            tags = tag_to_dict(inst)
            if tags.get(key) == value:
                wtags.append(inst["InstanceId"])
    return wtags

def group_by_env(resp):
    groups = defaultdict(list)
    for g in resp["Reservations"]:
        for inst in g["Instances"]:
            env = tag_to_dict(inst).get("Environment", "untagged")
            groups[env].append(inst["InstanceId"])
    return groups


main()

