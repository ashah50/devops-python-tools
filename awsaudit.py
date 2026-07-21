import argparse
import boto3

def get_regions(ec2):
    return [r["RegionName"] for r in ec2.describe_regions()["Regions"]]

def open_to_world(resp):
    risky = []
    for g in resp["SecurityGroups"]:
        for rule in g["IpPermissions"]:
            for cidr in rule["IpRanges"]:
                if cidr["CidrIp"] == "0.0.0.0/0":
                    risky.append((g["GroupName"], rule.get("FromPort", "ALL")))
    return risky

def audit_open_ports(all_regions):
    ec2 = boto3.client("ec2", region_name="us-east-1")
    regions = get_regions(ec2) if all_regions else ["us-east-1"]
    findings = {}
    for region in regions:
        regional = boto3.client("ec2", region_name=region)
        risky = open_to_world(regional.describe_security_groups())
        if risky:
            findings[region] = risky
    return findings

def untagged(resp):
    ids = []
    for r in resp["Reservations"]:
        for inst in r["Instances"]:
            if not inst.get("Tags"):
                ids.append((inst["InstanceId"], inst["InstanceType"]))
    return ids

def main():
    parser = argparse.ArgumentParser(description="Audit a real AWS account (read-only)")
    parser.add_argument("--regions", action="store_true", help="list enable regions")
    parser.add_argument("--open-ports", action="store_true", help="find security groups open to 0.0.0.0/0")
    parser.add_argument("--all-regions", action="store_true", help="with --open-ports, scan every region")
    parser.add_argument("--untagged", action="store_true", help="find untagged EC2 instances")
    args = parser.parse_args()

    if args.regions:
        ec2 = boto3.client("ec2", region_name="us-east-1")
        for name in sorted(get_regions(ec2)):
            print(" ",name)
    elif args.open_ports:
        findings = audit_open_ports(args.all_regions)
        if findings:
            for region, risky in findings.items():
                print(f"{region}:")
                for name, port in risky:
                    print(f"  {name}  port  {port}  OPEN TO WORLD")
        else:
            print("No security groups open to the world.")
    elif args.untagged:
         ec2 = boto3.client("ec2", region_name="us-east-1")
         found = untagged(ec2.describe_instances())
         print("UNTAGGED:", found if found else "none")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()