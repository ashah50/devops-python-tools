# DevOpsPythonTools                                                       
                                                                              
A set of command-line tools I built while learning Python for cloud/DevOps work. 
Each is a self-contained CLI that solves a real ops problem: log analysis, 
disk reporting, and read-only auditing of a live AWS account. 

## Tools                                                                    
                                                                             
### `awsaudit.py` — read-only AWS account auditor                           
Audits a real AWS account using boto3 (read-only; no resources are created 
or changed). 
                                                                                                                              
python3 awsaudit.py --regions                    # list enabled regions 
python3 awsaudit.py --open-ports                 # security groups open to 
0.0.0.0/0 (us-east-1)
python3 awsaudit.py --open-ports --all-regions   # scan every region
python3 awsaudit.py --untagged                   # EC2 instances with no 
tags 
python3 awsaudit.py --buckets                    # S3 bucket inventory (object count + size)
Finds security groups exposed to the internet and untagged instances —
common compliance and cost-hygiene checks. 
                                        
logparse.py — log file analyzer 

python3 logparse.py sample.log                   # count lines per level
python3 logparse.py sample.log --level ERROR     # filter to one level
python3 logparse.py sample.log --top 3           # most common messages
python3 logparse.py sample.log --group           # messages grouped by level
python3 logparse.py sample.log --rank 2          # most frequent levels

dureport.py — disk usage reporter 

python3 dureport.py ~/somedir --count            # files per extension
python3 dureport.py ~/somedir --size             # total size per extension
python3 dureport.py ~/somedir --top 5            # biggest files
python3 dureport.py ~/somedir --unique           # distinct extensions

boto3 learning scripts 

aws_demo.py, aws_sg.py (mock AWS via moto) and aws_live.py show the
progression from mocked to real AWS API calls.

Setup 

python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt 

For the AWS tools, configure credentials with aws configure (an IAM user with read-only access is
sufficient)
  
Skills demonstrated 
                                        
Python (functions, comprehensions, collections), argparse CLIs, pathlib,
the AWS SDK (boto3), mocking with moto, IAM/least-privilege, and multi-region API traversal. 
