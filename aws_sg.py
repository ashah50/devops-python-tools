import boto3
from moto import mock_aws

@mock_aws
def main():
    ec2 = boto3.client("ec2", region_name="us-east-1")

    # setup: a group open to the world on SSH (the planted risk)
    sg = ec2.create_security_group(GroupName="web", Description="web")
    ec2.authorize_security_group_ingress(GroupId=sg["GroupId"], IpPermissions=[{"IpProtocol": "tcp", "FromPort": 22, "ToPort": 22, "IpRanges": [{"CidrIp": "0.0.0.0/0"}]}])

    resp = ec2.describe_security_groups()
    print("OPEN TO WORLD:", open_to_world(resp))


def open_to_world(resp):
    risky = []
    for g in resp["SecurityGroups"]:
        for rule in g["IpPermissions"]:
            for cidr in rule["IpRanges"]:
                if cidr["CidrIp"] == "0.0.0.0/0":
                    port = rule.get("FromPort", "ALL")
                    risky.append((g["GroupName"], port))
    return risky



main()