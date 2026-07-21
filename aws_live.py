import boto3

def main():
    ec2 = boto3.client("ec2", region_name="us-east-1")
    resp = ec2.describe_regions()

    regions = [r["RegionName"] for r in resp["Regions"]]
    print(f"{len(regions)} regions:")
    for name in sorted(regions):
        print(" ", name)

    resp = ec2.describe_security_groups()
    print("SG count:", len(resp["SecurityGroups"]))
    print("OPEN TO WORLD:", open_to_world(resp))
    print("MULTI-REGION AUDIT:", audit_all_regions())

def open_to_world(resp):
    risky = []
    for g in resp["SecurityGroups"]:
        for rule in g["IpPermissions"]:
            for cidr in rule["IpRanges"]:
                if cidr["CidrIp"] == "0.0.0.0/0":
                    port = rule.get("FromPort", "ALL")
                    risky.append((g["GroupName"], port))
    return risky

def audit_all_regions():
    ec2 = boto3.client("ec2", region_name="us-east-1")
    regions = [r["RegionName"] for r in ec2.describe_regions()["Regions"]]
    findings = {}
    for region in regions:
        regional = boto3.client("ec2", region_name=region) # <-- NEW client, THIS region
        resp = regional.describe_security_groups()
        risky = open_to_world(resp)
        if risky:    # only for regions WITH issues
            findings[region] = risky
    return findings


main()