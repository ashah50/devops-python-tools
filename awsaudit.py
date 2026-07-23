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

def bucket_report():
    s3 = boto3.client("s3", region_name="us-east-1")
    buckets = [b["Name"] for b in s3.list_buckets()["Buckets"]]  # bucket reach-in
    report = {}
    for name in buckets:
        objs = s3.list_objects_v2(Bucket=name).get("Contents", [])  # .get guard for empty
        total = sum(o["Size"] for o in objs)  # sum + reach-in
        report[name] = (len(objs), total)
    return report

def is_public(s3, bucket):
    acl = s3.get_bucket_acl(Bucket=bucket)
    for grant in acl["Grants"]:
        uri = grant.get("Grantee", {}).get("URI", "")
        if uri.endswith("AllUsers"):
            return True
    return False

def public_buckets():
    s3 = boto3.client("s3", region_name="us-east-1")
    buckets = [b["Name"] for b in s3.list_buckets()["Buckets"]]
    return [name for name in buckets if is_public(s3, name)]

def main():
    parser = argparse.ArgumentParser(description="Audit a real AWS account (read-only)")
    parser.add_argument("--regions", action="store_true", help="list enable regions")
    parser.add_argument("--open-ports", action="store_true", help="find security groups open to 0.0.0.0/0")
    parser.add_argument("--all-regions", action="store_true", help="with --open-ports, scan every region")
    parser.add_argument("--untagged", action="store_true", help="find untagged EC2 instances")
    parser.add_argument("--buckets", action="store_true", help="inventory S3 buckets (object count + size)")
    parser.add_argument("--public-buckets", action="store_true", help="find S3 buckets open to the public")
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
    elif args.buckets:
        report = bucket_report()
        if report:
            for name, (count,size) in report.items():
                print(f"{name}: {count} objects, {size} bytes")
        else:
            print("No buckets.")
    elif args.public_buckets:
        found = public_buckets()
        print("PUBLIC BUCKETS:", found if found else "none")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()