#!/usr/bin/env python3
import json
import os
from datetime import datetime
from pathlib import Path

import boto3
from botocore.exceptions import ProfileNotFound
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = REPO_ROOT / ".env.local"
load_dotenv(ENV_FILE)

AWS_PROFILE = os.getenv("AWS_PROFILE", "tmf-dev")
AWS_REGION = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "us-east-1"
AWS_BUCKET = os.getenv("AWS_S3_BUCKET", "tmf-webhook-payloads-dev")
AWS_PREFIX = os.getenv("AWS_S3_PREFIX", "webhooks/")

try:
    session = boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)
except ProfileNotFound:
    # Fall back to default credentials chain if profile is missing
    session = boto3.Session(region_name=AWS_REGION)

s3 = session.client("s3")

# List latest files
resp = s3.list_objects_v2(Bucket=AWS_BUCKET, Prefix=AWS_PREFIX, MaxKeys=20)
objects = sorted(resp.get("Contents", []), key=lambda x: x["LastModified"], reverse=True)

print("Latest 10 webhook payloads in S3:\n")
for i, obj in enumerate(objects[:10], 1):
    key = obj["Key"]
    size = obj["Size"]
    mod_time = obj["LastModified"].strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"  {i:2}. {key.split('/')[-1]} ({size} bytes) - {mod_time}")

print(f"\nTotal files in S3: {len(objects)}")

# Show the MOST RECENT file
if objects:
    latest_key = objects[0]["Key"]
    latest_obj = s3.get_object(Bucket=AWS_BUCKET, Key=latest_key)
    data = json.loads(latest_obj["Body"].read())

    webhook_type = "Transcript" if "transcript" in str(data).lower() else "Calendar"

    print("\nLatest webhook payload (MOST RECENT):")
    print(f"   File: {latest_key.split('/')[-1]}")
    print(f"   Type: {webhook_type}")
    if "resourceData" in data:
        resource = data["resourceData"].get("resource", "N/A")
    else:
        resource = data.get("resource", "N/A")
    print(f"   Resource: {resource[:70]}...")
